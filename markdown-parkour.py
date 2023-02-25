#!/usr/bin/env python

# set up logging
import logging, os
logging.basicConfig(level=os.environ.get('LOGLEVEL', 'WARNING').upper())

# python libraries
import json
import sys
import traceback

# pip install
from mistletoe import Document
from mistletoe.ast_renderer import ASTRenderer

# element types
HEADING = 'Heading'
LIST = 'List'
LISTITEM = 'ListItem'
PARAGRAPH = 'Paragraph'
THEMATICBREAK = 'ThematicBreak'

# common keys
CHILDREN = 'children'
CONTENT = 'content'
LEVEL = 'level'

# Define a parse error handler
class ParseError(Exception):
    pass

profile = {}

# search for next element of type='type', and optionally, content matching 'content'
def get_next(elements, type, content=None):
    print(f"searching for a '{type}' element with content containing '{content}'")
    while elements:
        next = elements.pop(0)
        if next['type'] == type and (not content or content==get_content(next)):
            print(f"found '{type}' with content matching '{content}'")
            return elements, next
    return [], None

# search for heading with 'level', and optionally, content matching 'content'
def get_next_heading(elements, level, content=None):
    print(f"searching for H{level} with content containing '{content}'")
    while elements:
        elements, heading = get_next(elements, HEADING)
        if heading and heading[LEVEL] == level and (not content or content==get_content(heading)):
            print(f"found H{level} with content matching '{content}'")
            return elements, heading
    raise ParseError(f"Heading level {level} not found")

def get_content(element):
    return element[CHILDREN][0][CONTENT]

def get_listitem_content(listitem):
    return listitem[CHILDREN][0][CHILDREN][0][CONTENT]

def get_listitem_sublist(listitem):
    return listitem[CHILDREN][1:][0]

def parse_profile(ast):
    ast = json.loads(ast)
    elements = ast[CHILDREN]

    # get name from H1
    elements, heading = get_next_heading(elements, 1)
    profile['name'] = get_content(heading)
    print(f"name: {profile['name']}")

    # check first paragraph for page type
    elements, paragraph = get_next(elements, PARAGRAPH)
    if '[[People]]' not in get_content(paragraph):
        raise ParseError("Not a profile page")

    # find specific H2 heading
    elements, heading = get_next_heading(elements, 2, 'My current tools and practices')

    # find a list
    print("\n\ntools or practices")
    elements, list = get_next(elements, LIST)
    listitems = list[CHILDREN]
    while listitems:
        listitems, listitem = get_next(listitems, LISTITEM)
        print(f"tool or practice sentence: {get_listitem_content(listitem)}")

    # find specific H2 heading
    elements, heading = get_next_heading(elements, 2, 'Thinking Tool Ratings')
    
    # find a list
    print("\n\ntools and ratings")
    elements, list = get_next(elements, LIST)
    tools = list[CHILDREN]
    while tools:
        tools, tool = get_next(tools, LISTITEM)
        print(f"tool string: {get_listitem_content(tool)}")
        ratings = get_listitem_sublist(tool)[CHILDREN]
        while ratings:
            ratings, rating = get_next(ratings, LISTITEM)
            print(f"rating string: {get_listitem_content(rating)}")

def main():
    try:
        # process all files in argv
        for filename in sys.argv[1:]:
            with open(filename, 'r') as infile:
                with ASTRenderer() as renderer:
                    doc = Document(infile.readlines())
                    ast = renderer.render(doc)
                    parse_profile(ast)
    except ParseError as err:
        sys.stderr.write("\n\nParse error: {}.\n\n".format(err));
        sys.exit(1)
    except Exception as err:
        traceback.print_exc(err)
#        sys.stderr.write("\n\nError: {}\n\n".format(err));

if __name__ == "__main__":
    exit(main())
