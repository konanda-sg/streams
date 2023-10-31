#!/usr/bin/env python3

# EPG merger
# Created by:  @thefirefox12537

import glob
import json
import gzip
import shutil
import requests
import threading
import platform, os, re, sys
import xml.dom.minidom as dom
import lxml.etree as et

import argparse

parser = argparse.ArgumentParser();
parser.add_argument('--source', required=True, help='EPG source');
parser.add_argument('-o', '--target-epgxml', required=True, help='EPG output');
parser.add_argument('-t', '--norm-tmp', action='store_true', help='Do not remove temporary files');
parser.add_argument('-z', '--compress', action='store_true', help='With GZip compressing');
gen_info = parser.add_argument_group('(Optional) EPG Generated Information');
gen_info.add_argument('--gen-name', help='Generated name');
gen_info.add_argument('--gen-url', help='Generated URL');
args = parser.parse_args();

tmpdir = os.environ['TEMP'] if platform.system() == 'Windows' else ('{}' if os.path.isdir('{}') else '/var{}').format('/tmp');
tmpdir = tmpdir if os.path.isdir(tmpdir) else os.sep.join(['..', 'tmp']);
epg_target = args.target_epgxml + ('.gz' if args.compress else '');

def merge(tree, tagname, attrib):
  print(f'Merging {tagname}...');
  files = glob.glob(os.sep.join([tmpdir, '*.xml']));
  for file in files:
    try:
      srctree = et.parse(file);
      for child in srctree.getroot():
        if tagname in child.tag:
          source_dir = os.path.dirname(args.source);
          base_file = '{}.json'.format(os.path.basename(file));
          epgid = os.sep.join([source_dir, base_file]);
          if os.path.exists(epgid):
            epgid = json.loads(open(epgid).read());
            for read in epgid:
              if child.attrib[attrib] == read['origin']:
                child.attrib[attrib] = read['channel_id'];
                if 'channel' == tagname:
                  found = child.find('display-name');
                  found.text = read['channel_name'];
          tree.append(child);
    except:
      print('Skipping:', file);

if __name__ == '__main__':
  files = [];
  urls = [];

  if not os.path.exists(tmpdir):
    os.makedirs(tmpdir);
  if os.path.exists(args.target_epgxml):
    os.remove(args.target_epgxml);
  if not os.path.exists(args.source):
    raise FileNotFoundError(f'{args.source} is not exist');

  with open(args.source, mode='r') as epgsrc:
    for text in re.split(r'[\r\n]+', epgsrc.read()):
      if re.findall(r'^http[^\s]+.xml', text):
        urls.append(text);
      elif not re.findall(r'^$', text):
        files.append(text);
  for url, name in zip(urls, files):
    epgxml = os.sep.join([tmpdir, name]);
    if not os.path.exists(epgxml):
      try:
        print(f'Downloading {name}...');
        get = requests.get(url, allow_redirects=True);
        open(epgxml, mode='wb').write(get.content);
      except:
        print(f'Skipping download: {name}');

  gen_name = args.gen_name if args.gen_name else 'thefirefox12537';
  gen_url = args.gen_url if args.gen_url else 'https://thefirefox12537.github.io';
  tree = et.Element('tv', {
    'generator-info-name': f'EPG generated by {gen_name}',
    'generator-info-url': gen_url
  });
  merge(tree, tagname='channel', attrib='id');
  merge(tree, tagname='programme', attrib='channel');

  print('Parsing data...');
  tostring = et.tostring(tree, encoding='UTF-8', method='xml', xml_declaration=True);
  parsestring = dom.parseString(tostring).toprettyxml(indent='', encoding='UTF-8');
  output = re.sub(b'\n\n', b'', parsestring);

  print('Creating file...');
  with pgzip.open(epg_target, mode='wb', thread=0, blocksize=2*10**8) if args.compress \
  else open(epg_target, mode='wb') as epg:
    epg.write(output);
    epg.close();

  if not args.norm_tmp:
    print('Removing temporary files...');
    if tmpdir == os.sep.join(['..', 'tmp']):
      shutil.rmtree(tmpdir);
    else:
      for name in files:
        epgxml = os.sep.join([tmpdir, name]);
        os.remove(epgxml);

  sys.exit();
