import json
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from formgen import generate_form
from formgen.gen2 import generate_form as generate_form_v2
from formgen.gen2.script import script as generate_form_v2_script
from formgen.gen1.schema import Types
from test import TestModel, BaseSubModelN1, BaseSubModelN2, Enumed

base = """
<!DOCTYPE html>

<html lang="ru">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-GLhlTQ8iRABdZLl6O3oVMWSktQOp6b7In1Zl3/Jr59b6EGGoI1aFkw7cmDA6j6gD" crossorigin="anonymous">
        
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" />
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/select2-bootstrap-5-theme@1.3.0/dist/select2-bootstrap-5-theme.min.css" />

        <style>
            html {{
                position: relative;
                min-height: 100%;
            }}

            body {{
                margin-top: 48px; /* Margin top by header height */
                margin-bottom: 60px; /* Margin bottom by footer height */
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="mb-3">
                {body}
            </div>
        </div>

        <script src="https://code.jquery.com/jquery-1.10.2.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js" integrity="sha384-w76AqPfDkMBDXo30jS1Sgez6pr3x5MlQ1ZAGC+nuZB+EYdgRZgiwxhTBTkF7CXvN" crossorigin="anonymous"></script>
        <script src="https://unpkg.com/easymde/dist/easymde.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
        {scripts}
    </body>
</html>
"""  # noqa: E501

scripts = f"""
<script>
{generate_form_v2_script}
</script>
"""  # noqa: E501

app = FastAPI()


@app.get("/")
def load_test() -> HTMLResponse:
    test_model = TestModel(
        some_str="some_str...",
        sub=BaseSubModelN2(integer=-1),
        description="test",
        description_html="<h1> test </h1>",
        some_bool=False,
        sub_1=BaseSubModelN1(integer=-2),
        some_unitialized_list=["1", "2"],
        some_enum=Enumed.val3,
    )

    try:
        form = generate_form_v2(
            model_type=TestModel,
            model=test_model,
            form_id="test-form",
            # values=test_model.dict(),
            # overrides={
            #     "description": Types.textarea,
            #     "description_html": Types.html,
            #     "sub": Types.class_,
            #     "sub_1": Types.class_,
            # },
            # attribs={
            #     "some_id": {"readonly": True},
            #     # "sub": {"classtype": ["readonly"]},
            # },
        )
    except Exception as ex:  # noqa: PIE786, BLE001, W0703
        form = f"<pre>{ str(ex) }</pre>"

    body = f"{form}\n\n"
    return HTMLResponse(base.format(body=body, scripts=scripts))


# @app.get("/j")
# def load_json() -> HTMLResponse:
#     schema = json.load(open("./config_schema.json", encoding="utf-8"))  # noqa: SIM115, R1732, PTH123

#     try:
#         form = generate_form(
#             schema,
#             form_id="test1-form",
#             overrides={
#                 #
#             },
#             attribs={
#                 # "sub": {"classtype": ["readonly"]},
#             },
#         )
#     except Exception as ex:  # noqa: PIE786, BLE001, W0703
#         form = f"<pre>{ str(ex) }</pre>"

#     body = f"{form}\n\n <pre> {json.dumps(schema, indent=4)} </pre>"
#     return HTMLResponse(base.format(body=body, scripts=scripts))


@app.post("/")
def test(inp: TestModel) -> TestModel:
    return inp
