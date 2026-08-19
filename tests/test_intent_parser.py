import pytest

from llm.intent_parser import LLMIntentParser


@pytest.fixture
def parser():
    parser = LLMIntentParser()
    parser.client = None
    parser.is_configured = False
    return parser


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "non troppo pesante, voglio qualcosa di leggero",
            {"body": lambda mood: mood["body"] <= -3.0},
        ),
        (
            "non voglio nulla di pesante",
            {"body": lambda mood: mood["body"] < 0},
        ),
        (
            "non voglio una cosa troppo leggera",
            {"body": lambda mood: mood["body"] > 0},
        ),
        (
            "niente di elaborato, non voglio spendere troppo tempo",
            {"time": lambda mood: mood["time"] <= -3.0},
        ),
        (
            "senza fretta, voglio cucinare con calma",
            {"time": lambda mood: mood["time"] >= 2.0},
        ),
        (
            "non ho fretta, posso stare ai fornelli",
            {"time": lambda mood: mood["time"] > 0},
        ),
        (
            "molto gustoso e super saporito",
            {"taste": lambda mood: mood["taste"] >= 4.0},
        ),
        (
            "non troppo piccante, sapori delicati",
            {"taste": lambda mood: mood["taste"] < 0},
        ),
        (
            "davvero salutare e detox",
            {"mental": lambda mood: mood["mental"] <= -3.0},
        ),
        (
            "niente sgarri, qualcosa di sano",
            {"mental": lambda mood: mood["mental"] < 0, "body": lambda mood: mood["body"] <= 0},
        ),
        (
            "super confortante e coccoloso",
            {"mental": lambda mood: mood["mental"] >= 4.0, "body_absent": lambda mood: "body" not in mood},
        ),
        (
            "voglio qualcosa di squisitissimo",
            {"taste": lambda mood: mood["taste"] >= 4.0},
        ),
        (
            "senza melanzane, con pollo e patate",
            {"ingredients": lambda ingredients: "chicken" in ingredients and "potatoes" in ingredients},
        ),
        (
            "non mi piace il pesce, voglio pasta e pomodoro",
            {"exclude_ingredients": lambda excluded: "fish" in excluded},
        ),
        (
            "sono allergico a noci e lattosio",
            {"exclude_ingredients": lambda excluded: "nuts" in excluded or "dairy" in excluded},
        ),
        (
            "evito il pesce e il latte",
            {"exclude_ingredients": lambda excluded: "fish" in excluded or "dairy" in excluded},
        ),
        (
            "molto veloce, super economico e con pollo in frigo",
            {"time": lambda mood: mood["time"] <= -3.0, "price": lambda mood: mood["price"] <= -3.0},
        ),
        (
            "cena tra amici, molto gustosa ma non troppo pesante, sotto le 500 kcal",
            {"taste": lambda mood: mood["taste"] >= 3.0, "max_calories": lambda value: value == 500},
        ),
        (
            "vorrei una cena classica senza fretta e niente di elaborato",
            {"time": lambda mood: mood["time"] >= 2.0},
        ),
        (
            "pranzo leggero e molto salutare, voglio evitare il glutine",
            {"body": lambda mood: mood["body"] <= -3.0, "tags_required": lambda tags: "gluten-free" in tags},
        ),
        (
            "poco tempo e budget, con tofu, cipolla e broccoli, senza lattosio",
            {"time": lambda mood: mood["time"] <= -3.0, "price": lambda mood: mood["price"] <= -3.0, "tags_required": lambda tags: "dairy-free" in tags},
        ),
        (
            "qualcosa di davvero speciale ma economico",
            {"taste": lambda mood: mood["taste"] >= 3.0, "price": lambda mood: mood["price"] <= -3.0},
        ),
        (
            "stanco dopo lo studio, voglio comfort food molto veloce con pollo e aglio",
            {"mental": lambda mood: mood["mental"] >= 3.0, "time": lambda mood: mood["time"] <= -3.0, "body_absent": lambda mood: "body" not in mood},
        ),
        (
            "mi piace il classico, non troppo speziato",
            {"modification": lambda mood: mood["modification"] <= -2.0},
        ),
        (
            "niente di classico, voglio cambiare",
            {"modification": lambda mood: mood["modification"] > 0},
        ),
        (
            "sono stressato, voglio pasta cremosa e niente di detox",
            {
                "mental": lambda mood: mood["mental"] > 0,
                "taste": lambda mood: mood["taste"] > 0,
                "ingredients": lambda ingredients: "pasta" in ingredients,
            },
        ),
        (
            "ho tempo e voglia di sperimentare, ma deve restare leggero",
            {
                "time": lambda mood: mood["time"] > 0,
                "modification": lambda mood: mood["modification"] > 0,
                "body": lambda mood: mood["body"] < 0,
            },
        ),
        (
            "mi sento leggero, voglio qualcosa di fresco e poco impegnativo",
            {"body": lambda mood: mood["body"] < 0, "time": lambda mood: mood["time"] < 0},
        ),
        (
            "oggi voglio comfort food ricco ma non troppo lento",
            {
                "body": lambda mood: mood["body"] > 0,
                "mental": lambda mood: mood["mental"] > 0,
                "time": lambda mood: mood["time"] < 0,
            },
        ),
        (
            "non ho voglia di stare ai fornelli, ma voglio un gusto intenso",
            {"time": lambda mood: mood["time"] < 0, "taste": lambda mood: mood["taste"] > 0},
        ),
        (
            "voglio sapori delicati, niente di troppo speziato",
            {"taste": lambda mood: mood["taste"] < 0},
        ),
        (
            "qualcosa di elegante ma senza spendere troppo",
            {"taste": lambda mood: mood["taste"] > 0, "price": lambda mood: mood["price"] < 0},
        ),
        (
            "non deve essere costoso, però voglio una ricetta speciale",
            {"price": lambda mood: mood["price"] < 0, "taste": lambda mood: mood["taste"] > 0},
        ),
        (
            "ricco, costoso, elaborato e sperimentale",
            {
                "body": lambda mood: mood["body"] > 0,
                "price": lambda mood: mood["price"] > 0,
                "time": lambda mood: mood["time"] > 0,
                "modification": lambda mood: mood["modification"] > 0,
            },
        ),
        (
            "vojo una pasta al pomodoroo con pane e formaggio, ma senza pesce",
            {"ingredients": lambda ingredients: "pasta" in ingredients and "tomato" in ingredients, "exclude_ingredients": lambda excluded: "fish" in excluded},
        ),
        (
            "sono allergico al pesce e alle noci, vorrei pasta al pomodoro senza formaggio",
            {
                "ingredients": lambda ingredients: set(ingredients) == {"pasta", "tomato"},
                "exclude_ingredients": lambda excluded: set(excluded) == {"cheese", "fish", "nuts"},
            },
        ),
        (
            "ho solo riso, uova e carote in dispensa, zero voglia di cucinare per ore",
            {
                "ingredients": lambda ingredients: set(ingredients) == {"carrot", "egg", "rice"},
                "time": lambda mood: mood["time"] < 0,
            },
        ),
        (
            "vogli un pranzoo light ma con molta proteina",
            {"body": lambda mood: mood["body"] <= -3.0, "min_protein_pct": lambda value: value is not None},
        ),
    ],
)
def test_parser_covers_negations_intensifiers_and_exclusions(parser, text, expected):
    intent = parser.parse_query(text)

    for field, assertion in expected.items():
        value = intent.get(field)
        if field in {"ingredients", "exclude_ingredients", "tags_required"}:
            assert assertion(value), f"{field} mismatch for {text}: {value}"
        else:
            assert assertion(intent["mood"] if field != "max_calories" and field != "min_protein_pct" else value), f"{field} mismatch for {text}: {value}"


def test_parser_keeps_existing_schema_fields(parser):
    intent = parser.parse_query("qualcosa di molto gustoso ma leggero")

    assert set(intent.keys()) >= {
        "ingredients",
        "mood",
        "max_calories",
        "min_protein_pct",
        "tags_required",
        "profile_name",
        "exclude_ingredients",
    }
    assert intent["exclude_ingredients"] is None or isinstance(intent["exclude_ingredients"], list)


@pytest.mark.parametrize(
    ("text", "assertion"),
    [
        (
            "sono al verde, voglio spendere il minimo indispensabile",
            lambda intent: intent["mood"]["price"] < 0,
        ),
        (
            "voglio ingredienti costosi e ricercati",
            lambda intent: intent["mood"]["price"] > 0,
        ),
        (
            "ho bisogno di una coccola",
            lambda intent: "mental" in intent["mood"]
            and intent["mood"]["mental"] > 0
            and "body" not in intent["mood"],
        ),
        (
            "voglio spendere poco",
            lambda intent: intent["mood"]["price"] < 0,
        ),
        (
            "sono di corsa",
            lambda intent: intent["mood"]["time"] < 0,
        ),
        (
            "niente di tradizionale, sorprendimi",
            lambda intent: intent["mood"]["modification"] > 0,
        ),
        (
            "voglio qualcosa di ricco di proteine, senza carboidrati",
            lambda intent: "taste" not in (intent["mood"] or {})
            and "body" not in (intent["mood"] or {})
            and intent["min_protein_pct"] is not None,
        ),
        (
            "voglio un piatto ricco e goloso, che si scioglie in bocca",
            lambda intent: intent["mood"].get("taste", 0) > 0,
        ),
        (
            "cena tra amici: qualcosa di molto gustoso e un po' speciale, ma non troppo caro",
            lambda intent: intent["mood"].get("taste", 0) > 0
            and intent["mood"].get("price", 0) < 0,
        ),
        (
            "non voglio niente di tradizionale, sorprendimi con sapori speziati",
            lambda intent: intent["mood"].get("modification", 0) > 0
            and intent["mood"].get("taste", 0) > 0,
        ),
    ],
)
def test_fallback_parser_requested_regressions(parser, text, assertion):
    intent = parser.parse_query(text)

    assert assertion(intent), f"intent mismatch for {text}: {intent}"
