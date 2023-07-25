Endpoint: /ukaz_pozici
HTTP Method: POST
Request Headers:
    Content-Type: application/json
    Request Body:
Request Body:
{
    "vzor": "nazev_vzoru",
    "pozice": "nazev_pozice"
}
Response:
{
    "vzor_pozice": "BASE64_ENCODED_IMAGE_DATA"
}

Endpoint: /nalep_obrazek
HTTP Method: POST
Request Headers:
    Content-Type: application/json
    Request Body:
Request Body:
{
    "vzor": "nazev_vzoru",
    "pozice": "nazev_pozice",
    "obrazek": "BASE64_ENCODED_IMAGE_DATA"
}
Response:
{
    "vzor_s_obrazkem": "BASE64_ENCODED_IMAGE_DATA"
}

