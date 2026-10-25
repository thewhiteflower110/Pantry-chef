import streamlit as st
import yaml
import os

st.set_page_config(page_title="Pantry Recipe Finder", page_icon="🍳", layout="centered")

st.title("🍳 Pantry Recipe Finder")
st.markdown("Find recipes based on ingredients in your kitchen using your local YAML database.")

# --- Sidebar: Configuration & Filters ---
st.sidebar.header("📁 Database Configuration")
yaml_path = st.sidebar.text_input("Path to recipes.yaml", value="recipes.yaml")

# Load recipes from path
def load_recipes(path):
    if not os.path.exists(path):
        return None, f"File not found at: `{path}`. Please check the path."
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return data.get("recipes", []), None
    except Exception as e:
        return None, f"Error parsing YAML file: {e}"

recipes, error = load_recipes(yaml_path)

if error:
    st.error(error)
    st.info("""
    💡 Ensure your YAML file includes a `type` field (e.g., dinner, lunch, snack, dessert):
    ```yaml
    recipes:
      - name: 'Grilled Cheese'
        type: 'snack'
        ingredients:
          - bread
          - butter
          - cheese
        instructions: 'Butter bread and grill with cheese.'
    ```
    """)
else:
    st.sidebar.success(f"Loaded {len(recipes)} recipes successfully!")

    # Extract unique types for filtering
    all_types = sorted(list(set(r.get("type", "Uncategorized").strip().capitalize() for r in recipes)))
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🍽️ Filter Options")
    selected_type = st.sidebar.selectbox("Filter by Meal Type", ["All"] + all_types)

    # Extract all unique ingredients from the recipes database
    db_ingredients = set()
    for recipe in recipes:
        for ing in recipe.get("ingredients", []):
            db_ingredients.add(ing.strip().lower())

    # Common staples to ensure they are always easily selectable
    common_staples = ["bread", "butter", "cheese", "salt", "garlic", "eggs", "pepper", "olive oil"]
    combined_ingredient_options = sorted(list(db_ingredients.union(common_staples)))

    # --- Main UI: Pantry Selection ---
    st.subheader("🛒 Your Pantry")
    
    # Default selections if available in the options
    default_staples = [item for item in ["bread", "butter", "cheese", "eggs"] if item in combined_ingredient_options]
    
    selected_ingredients = st.multiselect(
        "Select ingredients you have (from staples & database):",
        options=combined_ingredient_options,
        default=default_staples
    )

    # Custom additional ingredients input for items not yet in the YAML database
    custom_input = st.text_input("Add other custom items (comma-separated)", placeholder="e.g. spinach, beans, mushrooms")
    custom_ingredients = [item.strip().lower() for item in custom_input.split(",") if item.strip()]
    
    # Combine active pantry items
    pantry = list(set(selected_ingredients + custom_ingredients))

    if pantry:
        st.caption(f"**Active Pantry:** {', '.join(pantry)}")
    else:
        st.warning("Please select or add at least one ingredient.")

    st.markdown("---")
    st.subheader("📖 Matching Recipes")

    # Filter recipes by type first
    active_recipes = recipes
    if selected_type != "All":
        active_recipes = [r for r in recipes if r.get("type", "").strip().capitalize() == selected_type]

    if pantry and active_recipes:
        pantry_set = {item.lower() for item in pantry}
        matches = []

        for recipe in active_recipes:
            recipe_ingredients = {ing.lower() for ing in recipe.get("ingredients", [])}
            available = recipe_ingredients.intersection(pantry_set)
            missing = recipe_ingredients - pantry_set

            if available:
                match_pct = round((len(available) / len(recipe_ingredients)) * 100)
                recipe_type = recipe.get("type", "General").capitalize()
                matches.append({
                    "name": recipe.get("name", "Unnamed Recipe"),
                    "type": recipe_type,
                    "match_percentage": match_pct,
                    "missing": list(missing),
                    "available": list(available),
                    "instructions": recipe.get("instructions", "No instructions provided.")
                })

        # Sort by best match percentage
        matches = sorted(matches, key=lambda x: x["match_percentage"], reverse=True)

        if not matches:
            st.info("No matching recipes found with your current ingredients and filter criteria.")
        else:
            for recipe in matches:
                with st.expander(f"✨ {recipe['name']} [{recipe['type']}] — {recipe['match_percentage']}% Match"):
                    if recipe['missing']:
                        st.markdown(f"❌ **Missing:** {', '.join(recipe['missing'])}")
                    else:
                        st.markdown("🎉 **You have all ingredients!**")
                    st.markdown(f"✅ **You have:** {', '.join(recipe['available'])}")
                    st.markdown(f"**Instructions:**\n{recipe['instructions']}")