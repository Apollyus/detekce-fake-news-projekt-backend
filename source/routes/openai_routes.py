from fastapi import APIRouter
import modules.api_call as oapi

router = APIRouter()

@router.get("/{prompt}")
def read_item(prompt: str):
    response = oapi.get_response(prompt)
    return {
        "response": response,
        "output_text": response.output_text
    }

@router.get("")
def read_item_query(prompt: str):
    response = oapi.get_response(prompt)
    return {
        "response": response,
        "output_text": response.output_text
    }
