#!/usr/bin/env python

# TftMap Builder v1.0.0 - https://github.com/peterkaminski/tftmap-builder

# Copyright 2023 Peter Kaminski. Licensed under MIT license, see accompanying LICENSE file.

# set up logging
import logging, os
logging.basicConfig(level=os.environ.get('LOGLEVEL', 'WARNING').upper())

# python libraries
import argparse
import json
from pathlib import Path
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
torps = set()
torp_sentences = {}

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
    return [], None

def get_content(element):
    try:
        return element[CHILDREN][0][CONTENT]
    except Exception as err:
        raise ParseError(err)

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
    profile = {}

    # get name from H1
    try:
        elements, heading = get_next_heading(elements, 1)
    except ParseError as err:
        return None
    profile['name'] = get_content(heading)
    logging.info(f"name: {profile['name']}")

    # check first paragraph for page type
    try:
        elements, paragraph = get_next(elements, PARAGRAPH)
        content = get_content(paragraph)
    except ParseError as err:
        return None
    if '[[People]]' not in content:
        return None

    # find specific H2 heading
    elements, heading = get_next_heading(elements, 2, 'My current tools and practices')

    if heading:
        # find a list
        logging.info("\n\ntools or practices")
        elements, list = get_next(elements, LIST)
        if list:
            listitems = list[CHILDREN]
            while listitems:
                listitems, listitem = get_next(listitems, LISTITEM)
                torp_sentence = get_listitem_content(listitem)
                logging.info(f"tool or practice sentence: {torp_sentence}")
                links = get_links(torp_sentence)
                torps.update(links)
                for link in links:
                    if link not in torp_sentences:
                        torp_sentences[link] = [[profile['name'],torp_sentence]]
                    else:
                        torp_sentences[link].append([profile['name'], torp_sentence])

    # find specific H2 heading
    elements, heading = get_next_heading(elements, 2, 'Thinking Tool Ratings')
    
    if heading:
        # find a list
        logging.info("\n\ntools and ratings")
        elements, list = get_next(elements, LIST)
        if list:
            tools = list[CHILDREN]
            while tools:
                tools, tool = get_next(tools, LISTITEM)
                logging.info(f"tool string: {get_listitem_content(tool)}")
                ratings = get_listitem_sublist(tool)[CHILDREN]
                while ratings:
                    ratings, rating = get_next(ratings, LISTITEM)
                    logging.info(f"rating string: {get_listitem_content(rating)}")

def read_torp_file(filename):
    torps = []

    with open(filename, 'r') as infile:
        with ASTRenderer() as renderer:
            doc = Document(infile.readlines())
            ast = renderer.render(doc)

    ast = json.loads(ast)
    elements = ast[CHILDREN]

    # find a list
    elements, list = get_next(elements, LIST)
    listitems = list[CHILDREN]
    while listitems:
        listitems, listitem = get_next(listitems, LISTITEM)
        # get target from first link
        targets = get_links(get_listitem_content(listitem))
        if len(targets):
               torps.append(targets[0])

    # all done
    return torps

def main():
    logging.debug("Initializing")

    argparser = init_argparse();
    args = argparser.parse_args();
    logging.debug("args: %s", args)

    # remember paths
    dir_map = os.path.abspath(args.directory)

    try:
        # get existing torps
        tools = read_torp_file(Path(dir_map) / "Tools.md")
        print(f"\n\n## Existing Index of Tools\n\n{tools}\n\n")
        practices = read_torp_file(Path(dir_map) / "Practices.md")
        print(f"## Existing Index of Practices\n\n{practices}\n\n")

        # process all files in argv
        print("## Files\n")
        for filename in Path(dir_map).glob('*.md'):
            with open(filename, 'r') as infile:
                with ASTRenderer() as renderer:
                    doc = Document(infile.readlines())
                    ast = renderer.render(doc)
                    profile = parse_profile(ast)
                    if profile is not None:
                        print("PROFILE")
                    print(filename)

        # now we have all tools or practices, and sentences
        print(f"\n\n## All Tools or Practices\n\n{torps}")
        print("\n\n## Torp Sentences\n")
        from pprint import pprint
        pprint(torp_sentences)

    except ParseError as err:
        sys.stderr.write("\n\nParse error: {}.\n\n".format(err));
        sys.exit(1)
    except Exception as err:
        print(f"TORP_SENTENCES\n\n{torp_sentences}\n====\n")
        traceback.print_exc(err)

if __name__ == "__main__":
    exit(main())
