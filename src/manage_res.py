#! /usr/bin/env python
# -*- coding: utf8 -*-

import json
import os
from collections import OrderedDict

'''json schema:
    [{
    "num_versions": 74,
    "url_citation": null,
    "title": "A fast learning algorithm for deep belief nets",
    "url": "http://www.mitpressjournals.org/doi/abs/10.1162/neco.2006.18.7.1527",
    "url_versions": "http://scholar.google.com/scholar?cluster=4412725301034087472&hl=en&as_sdt=1,5&as_vis=1",
    "year": "2006",
    "excerpt": "... (2015) Deep learning applications and challenges in big data analytics. Journal of Big Data 2.Online publication date: 1-Dec-2015. ... Yoshua Bengio, Honglak Lee. (2015) Editorial introductionto the Neural Networks special issue on Deep Learning of Representations. ...",
    "url_pdf": null,
    "num_citations": 3109,
    "cluster_id": "4412725301034087472",
    "authors": "GE Hinton, S Osindero, YW Teh - Neural computation",
    "url_citations": "http://scholar.google.com/scholar?cites=4412725301034087472&as_sdt=2005&sciodt=1,5&hl=en"
    }]'''


def import_json(file_name):
    with open(file_name) as input_file:
        return json.load(input_file)


def dump_json(file_name, data):
    with open(file_name, 'wr') as output_file:
        return json.dump(data, output_file)

'''Grapher json schema:
    {"4412725301034087472":{
    "num_versions": 74,
    "url_citation": null,
    "title": "A fast learning algorithm for deep belief nets",
    "url": "http://www.mitpressjournals.org/doi/abs/10.1162/neco.2006.18.7.1527",
    "url_versions": "http://scholar.google.com/scholar?cluster=4412725301034087472&hl=en&as_sdt=1,5&as_vis=1",
    "year": "2006",
    "excerpt": "... (2015) Deep learning applications and challenges in big data analytics. Journal of Big Data 2.Online publication date: 1-Dec-2015. ... Yoshua Bengio, Honglak Lee. (2015) Editorial introductionto the Neural Networks special issue on Deep Learning of Representations. ...",
    "url_pdf": null,
    "num_citations": 3109,
    "cluster_id": "4412725301034087472",
    "authors": "GE Hinton, S Osindero, YW Teh - Neural computation",
    "url_citations": "http://scholar.google.com/scholar?cites=4412725301034087472&as_sdt=2005&sciodt=1,5&hl=en"
    }}'''


def build_res_dict(res_list):
    return {str(x['cluster_id']): x for x in res_list if x['year'] is not None}


def authors_from_string(s):
    return [x.strip().encode('utf-8').decode('unicode_escape').encode('ascii', 'ignore') for x in s.split(
        ' - ')[0].replace(u'…', '').replace('...', '').strip(' - ,').split(',')]


def authors_of_article(article):
    return authors_from_string(article['authors'])


def build_authors_dict(res_dict):
    authors_dict = {}
    for key, value in res_dict.iteritems():
        authors_dict[key] = value['authors']
    return authors_dict


def build_authors_set(authors_dict):
    res = set([])
    for key, value in authors_dict.iteritems():
        res = res | set(authors_from_string(value))
    return res


def merge_results_lists(directory='results/'):
    cited_by_dict = get_cited_by_dict()
    res = {}
    for file_name in [x for x in os.listdir(directory) if x.endswith('.json')]:
        part_res = import_json(directory + file_name)
        part_res_dict = build_res_dict(part_res)
        for key, value in part_res_dict.iteritems():
            res[key] = value
            res[key]['authors_list'] = authors_of_article(value)
            if key in cited_by_dict.keys():
                res[key]['cited_by'] = cited_by_dict[key]
            else:
                res[key]['cited_by'] = []
    return res


def sort_articles(articles):
    keys = OrderedDict(
        sorted(articles.items(), key=lambda t: int(t[1]['year']))).keys()
    kkeys = keys
    for i in range(len(keys)):
        for j in range(i+1, len(keys)):
            if 'cited_by' in articles[kkeys[j]].keys():
                if keys[i] in articles[kkeys[j]]['cited_by']:
                    t = kkeys[j]
                    del kkeys[j]
                    kkeys.insert(i, t)
    return kkeys


def get_most_cited(num, d):
    res = {}
    for key, value in d.iteritems():
        if value['num_citations'] >= num:
            res[key] = value
    return res


def get_most_pertinent(phrase, d):
    res = {}
    for key, value in d.iteritems():
        if phrase in str(value).lower():
            res[key] = value
    return res


def citation_avg(d):
    elements = len(d.keys())
    sum_value = 0
    for key, value in d.iteritems():
        sum_value += value['num_citations']
    return sum_value / elements


def get_in_year(year, d):
    res = {}
    for key, value in d.iteritems():
        if value['year'] is not None and int(value['year']) == year:
            res[key] = value
    return res


def get_before_and_in_year(year, d, after_year=0):
    res = {}
    for key, value in d.iteritems():
        if value['year'] is not None and int(value['year']) <= year and int(value['year']) >= after_year:
            res[key] = value
    return res


def get_min_year(year, d):
    res = {}
    for key, value in d.iteritems():
        if value['year'] is not None and int(value['year']) >= year:
            res[key] = value
    return res


def save_res_list(d, file_name):
    res = []
    for key, value in d.iteritems():
        res.append(value)
    with open(file_name, 'wb') as f:
        json.dump(res, f)


def not_yet_done(tot_dict, directory='results/'):
    res = {}
    f_names = [x.split('.')[0]
               for x in os.listdir(directory) if x.endswith('.json')]
    for key, value in tot_dict.iteritems():
        if key not in f_names:
            res[key] = value
    return res


def get_cited_by_dict():
    res = {}
    dir1 = 'results/first res'
    dir2 = 'results/sec res'

    f_names1 = [x.split('.')[0]
                for x in os.listdir(dir1) if x.endswith('.json')]
    for f in f_names1:
        res[f] = [x for x in build_res_dict(
            import_json(dir1 + '/' + f + '.json')).keys() if x is not None]

    f_names2 = [x.split('.')[0]
                for x in os.listdir(dir2) if x.endswith('.json')]
    for f in f_names2:
        res[f] = [x for x in build_res_dict(
            import_json(dir2 + '/' + f + '.json')).keys() if x is not None]
    return res


def get_all_authors(articles):
    '''{'Joe Black': ['0132', '0212']}'''
    a_d = build_authors_dict(articles)
    a_S = []
    for k in sort_articles(articles):
        for a in authors_from_string(a_d[k]):
            if a not in a_S:
                a_S.append(a)
    return a_S


def get_max_cit_num(articles):
    m = 0
    for k, v in articles.iteritems():
        if m < int(v['num_citations']):
            m = int(v['num_citations'])
    return m


def get_min_and_max_year(articles):
    max_ = 0
    min_ = 2020
    for k, v in articles.iteritems():
        if max_ < int(v['year']):
            max_ = int(v['year'])
        if min_ > int(v['year']):
            min_ = int(v['year'])
    return min_, max_


def delete_uselss_records(directory, useless_authors_file='delete.txt'):
    with open(useless_authors_file) as f:
        useless_authors = [x.strip() for x in f.readlines()]

    for file_name in [x for x in os.listdir(directory) if x.endswith('.json')]:
        useful = {}
        d = build_res_dict(import_json(directory + file_name))
        for k, v in d.iteritems():
            useful_f = True
            for a in useless_authors:
                if a in v['authors']:
                    useful_f = False
            if useful_f:
                useful[k] = v
        dump_json(directory + file_name, [v for v in useful.itervalues()])


def author_citations(author, articles):
    count = 0
    for article in articles.itervalues():
        if author in article['authors']:
            count += 1
    return count


def max_author_citations(authors, articles):
    max_cits = 0
    for author in authors:
        count = 0
        for article in articles.itervalues():
            if author in article['authors']:
                count += 1
        if count > max_cits:
            max_cits = count
    return max_cits
