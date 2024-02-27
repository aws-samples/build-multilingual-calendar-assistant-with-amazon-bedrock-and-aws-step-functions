import pytest
import llm_output_parser

def test_parse_returns_json_1():
 
   input_string = '{"some":"json"}'

   result = llm_output_parser.parse(input_string)

   assert isinstance(result, dict)
   assert result == {"some":"json"}
   
def test_parse_returns_json_2():
 
   input_string = "some text before {\"key\": \"value\"} and some text after"

   result = llm_output_parser.parse(input_string)

   assert isinstance(result, dict)
   assert result == {"key":"value"}
   
def test_parse_returns_json_3():
 
   input_string = "some text before {\"key\": \"value\"} and some text after"

   result = llm_output_parser.parse(input_string)

   assert isinstance(result, dict)
   assert result == {"key":"value"}

def test_parse_handles_invalid_json():

   input_string = "{" 
  
   result = llm_output_parser.parse(input_string)
   
   assert result == None

def test_parse_strips_surrounding_text():

   input_string = 'before {"some":"json"} after'

   result = llm_output_parser.parse(input_string)

   assert result == {"some":"json"}
   
if __name__ == "__main__":
    test_parse_returns_json_1()
    test_parse_returns_json_2()
    test_parse_handles_invalid_json()
    test_parse_strips_surrounding_text()