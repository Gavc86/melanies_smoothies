import streamlit as st
import requests
import pandas as pd
from snowflake.snowpark.functions import col

# App title
st.title("Customize Your Smoothie 🍹")
st.write("Choose the fruits you want in your custom Smoothie!")

# Input for name
name_on_order = st.text_input('Name on Smoothie')
st.write('The name on your Smoothie will be:', name_on_order)

# Connect to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Load fruit options
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))
pd_df = my_dataframe.to_pandas()

# Multiselect for ingredients
ingredients_list = st.multiselect('Choose up to 5 ingredients:', pd_df['FRUIT_NAME'], max_selections=5)

if ingredients_list:
    # Build ingredient string exactly
    ingredients_string = " ".join(ingredients_list)

    # Show details for each selected fruit
    for fruit_chosen in ingredients_list:
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        st.write(f"The search value for {fruit_chosen} is {search_on}.")

        st.subheader(f"{fruit_chosen} Nutrition Information")
        response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_on}")

        if response.status_code == 200:
            st.dataframe(pd.DataFrame([response.json()]), use_container_width=True)
        else:
            st.error(f"Could not fetch nutrition data for {fruit_chosen}")

# Button to submit order
if st.button('Submit Order'):
    if not name_on_order:
        st.error("Please enter a name for your Smoothie before submitting.")
    elif not ingredients_list:
        st.error("Please choose at least one ingredient.")
    else:
        my_insert_stmt = f"""
            INSERT INTO smoothies.public.orders (INGREDIENTS, NAME_ON_ORDER, ORDER_FILLED)
            VALUES ('{ingredients_string}', '{name_on_order}', FALSE)
        """
        session.sql(my_insert_stmt).collect()
        st.success("Your Smoothie is ordered!")
