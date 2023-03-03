#!/usr/bin/env python

# TftMap Builder

# set up logging
import logging, os
logging.basicConfig(level=os.environ.get('LOGLEVEL', 'WARNING').upper())

# python libraries
import json
import re
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

# global variables
profile = {}
torps = set()

# set up argparse
def init_argparse():
    parser = argparse.ArgumentParser(description='Read Profiles, build Tools and Practices pages.')
    parser.add_argument('--directory', '-d', required=True, help='directory of source Markdown files')
    return parser

# search for next element of type='type', and optionally, content matching 'content'
def get_next(elements, type, content=None):
    logging.debug(f"searching for a '{type}' element with content containing '{content}'")
    while elements:
        next = elements.pop(0)
        if next['type'] == type and (not content or content==get_content(next)):
            logging.debug(f"found '{type}' with content matching '{content}'")
            return elements, next
    return [], None

# search for heading with 'level', and optionally, content matching 'content'
def get_next_heading(elements, level, content=None):
    logging.debug(f"searching for H{level} with content containing '{content}'")
    while elements:
        elements, heading = get_next(elements, HEADING)
        if heading and heading[LEVEL] == level and (not content or content==get_content(heading)):
            logging.debug(f"found H{level} with content matching '{content}'")
            return elements, heading
    raise ParseError(f"Heading level {level} not found")

def get_content(element):
    return element[CHILDREN][0][CONTENT]

def get_listitem_content(listitem):
    return listitem[CHILDREN][0][CHILDREN][0][CONTENT]

def get_listitem_sublist(listitem):
    return listitem[CHILDREN][1:][0]

def get_links(s):
    link_re = re.compile(r"\[\[ *([^\]]+) *\]\]")
    return re.findall(link_re, s)

def parse_profile(ast):
    ast = json.loads(ast)
    elements = ast[CHILDREN]

    # get name from H1
    elements, heading = get_next_heading(elements, 1)
    profile['name'] = get_content(heading)
    logging.info(f"name: {profile['name']}")

    # check first paragraph for page type
    elements, paragraph = get_next(elements, PARAGRAPH)
    if '[[People]]' not in get_content(paragraph):
        raise ParseError("Not a profile page")

    # find specific H2 heading
    elements, heading = get_next_heading(elements, 2, 'My current tools and practices')

    # find a list
    logging.info("\n\ntools or practices")
    elements, list = get_next(elements, LIST)
    listitems = list[CHILDREN]
    while listitems:
        listitems, listitem = get_next(listitems, LISTITEM)
        torp_sentence = get_listitem_content(listitem)
        logging.info(f"tool or practice sentence: {torp_sentence}")
        torps.update(get_links(torp_sentence))

    # find specific H2 heading
    elements, heading = get_next_heading(elements, 2, 'Thinking Tool Ratings')
    
    # find a list
    logging.info("\n\ntools and ratings")
    elements, list = get_next(elements, LIST)
    tools = list[CHILDREN]
    while tools:
        tools, tool = get_next(tools, LISTITEM)
        logging.info(f"tool string: {get_listitem_content(tool)}")
        ratings = get_listitem_sublist(tool)[CHILDREN]
        while ratings:
            ratings, rating = get_next(ratings, LISTITEM)
            logging.info(f"rating string: {get_listitem_content(rating)}")

def main():
    logging.debug("Initializing")

    argparser = init_argparse();
    args = argparser.parse_args();
    logging.debug("args: %s", args)

    try:
        # process all files in argv
        for filename in sys.argv[1:]:
            with open(filename, 'r') as infile:
                with ASTRenderer() as renderer:
                    doc = Document(infile.readlines())
                    ast = renderer.render(doc)
                    parse_profile(ast)
                    print(f"\n\nAll Tools and Practices\n{torps}")
    except ParseError as err:
        sys.stderr.write("\n\nParse error: {}.\n\n".format(err));
        sys.exit(1)
    except Exception as err:
        traceback.print_exc(err)

if __name__ == "__main__":
    exit(main())
