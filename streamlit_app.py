import streamlit as st
import requests
from snowflake.snowpark.functions import col
from snowflake.snowpark import Row

# --------------------------
# App title & intro
# --------------------------
st.title("🥤 Customize Your Smoothie")
st.write("Choose the fruits you want in your custom Smoothie!")

# --------------------------
# Input for name
# --------------------------
name_on_order = st.text_input('Name on Smoothie')
if name_on_order:
    st.write(f"✨ The name on your Smoothie will be: **{name_on_order}**")

# --------------------------
# Connect to Snowflake
# --------------------------
cnx = st.connection("snowflake")
session = cnx.session()

# Get fruit options with SEARCH_ON
fruit_options_df = session.table("smoothies.public.fruit_options") \
    .select(col('FRUIT_NAME'), col('SEARCH_ON'))

pd_df = fruit_options_df.to_pandas()

# --------------------------
# Multiselect for ingredients
# --------------------------
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    pd_df['FRUIT_NAME'].tolist(),
    max_selections=5
)

# --------------------------
# If ingredients selected, show nutrition info
# --------------------------
if ingredients_list:
    # Combine into one string for DB insert
    ingredients_string = ', '.join(ingredients_list)

    st.subheader("🥗 Nutrition Information")
    for fruit_chosen in ingredients_list:
        # Lookup API search value
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        st.write(f"🔎 **{fruit_chosen}** will be searched as `{search_on}`")

        # Fetch and display nutrition info
        response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_on}")
        if response.status_code == 200:
            st.dataframe(data=response.json(), use_container_width=True)
        else:
            st.error(f"❌ Could not fetch data for {fruit_chosen} ({search_on})")

    # --------------------------
    # Preview Order Summary
    # --------------------------
    st.subheader("📝 Order Summary")
    st.write(f"👤 Name on Order: **{name_on_order if name_on_order else '(not entered)'}**")
    st.write(f"🍓 Ingredients: {ingredients_string}")

    # --------------------------
    # Button to submit order
    # --------------------------
    if st.button('✅ Submit Order'):
        if not name_on_order:
            st.error("❌ Please enter a name for your Smoothie before submitting.")
        else:
            # Create a Row object for the order
            new_row = Row(
                INGREDIENTS=ingredients_string,
                NAME_ON_ORDER=name_on_order,
                ORDER_FILLED=False
            )
            # Insert into the orders table
            session.table("smoothies.public.orders").insert([new_row])
            st.success("🎉 Your Smoothie is ordered!")
