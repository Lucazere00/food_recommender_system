from utils.links import build_foodcom_url


def test_build_foodcom_url_with_id():
    recipe = {"id": 12345, "name": "Simple Pie"}
    url = build_foodcom_url(recipe)
    assert url == "https://www.food.com/recipe/simple-pie-12345"


def test_build_foodcom_url_slugifies_name():
    recipe = {"id": 987, "name": "Crème Brûlée: The Best!"}
    url = build_foodcom_url(recipe)
    # slug should remove accents, punctuation and lowercase
    assert url.startswith("https://www.food.com/recipe/creme-brulee-the-best-987")


def test_build_foodcom_url_without_id_uses_search():
    recipe = {"name": "Torta di mele"}
    url = build_foodcom_url(recipe)
    assert url.startswith("https://www.food.com/search/")
    assert "Torta+di+mele" in url or "torta+di+mele" in url
