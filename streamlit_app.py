import streamlit as st
import requests
from snowflake.snowpark.functions import col

# App title
st.title("Customize Your Smoothie 🥤")
st.write("Choose the fruits you want in your custom Smoothie!")

# Input for name
name_on_order = st.text_input('Name on Smoothie')
if name_on_order:
    st.write('The name on your Smoothie will be:', name_on_order)

# Connect to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Get fruit options with SEARCH_ON
fruit_options_df = session.table("smoothies.public.fruit_options") \
    .select(col('FRUIT_NAME'), col('SEARCH_ON'))

pd_df = fruit_options_df.to_pandas()

# Multiselect for ingredients
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    pd_df['FRUIT_NAME'].tolist(),
    max_selections=5
)

# If ingredients selected
if ingredients_list:
    # Combine into one string for DB insert
    ingredients_string = ', '.join(ingredients_list)

    for fruit_chosen in ingredients_list:
        # Lookup API search value
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        st.write(f"🔎 The search value for {fruit_chosen} is **{search_on}**.")

        # Fetch and display nutrition info
        st.subheader(f"{fruit_chosen} Nutrition Information")
        response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_on}")
        if response.status_code == 200:
            st.dataframe(data=response.json(), use_container_width=True)
        else:
            st.error(f"Could not fetch data for {fruit_chosen} ({search_on})")

    # Prepare the insert query safely
    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders (ingredients, name_on_order, order_filled)
        VALUES (%s, %s, FALSE)
    """

    # Button to submit order
    if st.button('Submit Order'):
        session.sql(my_insert_stmt, params=(ingredients_string, name_on_order)).collect()
        st.success("✅ Your Smoothie is ordered!")



