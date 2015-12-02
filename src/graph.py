#! /usr/bin/env python
# -*- coding: utf8 -*-


import cgi
from graphviz import Digraph
from colour import Color
from numpy import exp
from manage_res import get_all_authors, merge_results_lists, get_min_year
from manage_res import max_author_citations, get_most_cited, import_json
from manage_res import get_max_cit_num, get_min_and_max_year, build_res_dict
from manage_res import author_citations, sort_articles, get_in_year
from manage_res import get_before_and_in_year

MAX_EXP_X = 4
SIZE_MIN = 5
SIZE_MAX = 50
SIZE_AUTHOR = 0.3
SIZE_AUTH_MAX = 5
SIZE_AUTH_MIN = 1.5
MIN_CITATIONS = 0
MIN_YEAR = 1890
MIN_YEAR_LAYERS = 2009

EXPORT_ATTRS = [  # (name, format, view),
    ('500dlpapers', 'dot', False),
    ('500dlpapers', 'svg', False)]


def str_(pos):
    return str(pos[0]) + ',' + str(pos[1]) + '!'


def normalize(e, min_v, max_v):
    return (e-min_v)/(max_v - min_v)


def get_step(start, end, steps):
    return float(end - start)/steps


def exp2(x):
    return 2**x


def get_steps_list(start, end, steps):
    func = exp

    def get_x(s):
        return ((float(s) * MAX_EXP_X)/steps)
    expansion_factor = func(MAX_EXP_X)/(func(MAX_EXP_X)-1)
    y_shift = -1*func(-MAX_EXP_X)

    return [abs(round(start + (end-start) * (y_shift + func(get_x(s) - MAX_EXP_X)) * expansion_factor, 1)) for s in range(steps)]


def color_range(steps, start=Color("pink"), end=Color("red")):
    steps_l = tuple()
    for i in range(0, 3):
        steps_l = steps_l + (get_steps_list(start.rgb[i], end.rgb[i], steps),)
    color_range = []
    for s in range(steps):
        color_range.append(
            tuple([steps_l[i][s] for i in range(0, 3)]))
    return color_range


class Grapher(object):

    """docstring for Grapher"""

    def __init__(self):
        super(Grapher, self).__init__()
        self.authors = []
        self.all_articles = {}
        self.articles1L = {}
        self.articles2L = {}
        self.articles3L = {}
        self.style = {
            'graph': {'fontsize': '11',
                      'bgcolor': '#000000',
                      'label': 'dlsoa',
                      'graph_type': 'graph',
                      'size': '50',
                      'bgcolor': 'white',
                      'splines': 'true',
                      'overlap': 'false',
                      'ranksep': str(SIZE_MAX),
                      #'nodesep': str(2*SIZE_MAX),
                      'ordering': 'out',
                      'ratio': '1',
                      'rankdir': 'TB',
                      'concentrate': 'false',
                      #'nslimit1':'100'
                      },
            '1Lnode': {}}
        self.MAX_CIT_NUM = 0
        self.MAX_CIT_RATIO = 0
        self.MAX_CITS_AUTH = 0
        self.MIN_YEAR, self.MAX_YEAR = 0, 0
        self.node_colors = None

    def add_authors(self, authors):
        self.authors += authors

    def add_first_layer_articles(self, articles):
        self.articles1L = dict(self.articles1L.items() + articles.items())

    def add_second_layer_articles(self, articles):
        keys = self.articles1L.keys()
        for key, value in articles.iteritems():
            if key not in keys:
                self.articles2L[key] = value

    def add_third_layer_articles(self, articles):
        keys = self.articles1L.keys() + self.articles2L.keys()
        for key, value in articles.iteritems():
            if key not in keys:
                self.articles3L[key] = value

    def get_size_of_auth(self, a):
        cits = author_citations(a, self.all_articles)
        t = (0.0 + cits) / self.MAX_CITS_AUTH
        return SIZE_AUTH_MIN + t * (SIZE_AUTH_MAX - SIZE_AUTH_MIN)

    def get_size_of_art(self, key):
        cits = int(self.all_articles[key]['num_citations'])
        ratio = cits / \
            ((self.MAX_YEAR+1 - int(self.all_articles[key]['year'])))
        t = (0.0 + ratio) / self.MAX_CIT_RATIO
        return SIZE_MIN + t * (SIZE_MAX - SIZE_MIN)

    def get_color_of_node(self, key):
        t = int(self.all_articles[key]['year']) - self.MIN_YEAR
        return "%s" % Color(rgb=self.color_range[t]).get_hex_l()

    def add_authors_nodes(self, g, pos):
        for a in self.authors:
            size = self.get_size_of_auth(a)
            g.node(a,
                   group="authors",
                   # shape="star",
                   pos=str_(pos),
                   fixedsize="true",
                   style="filled",
                   fillcolor="#00ff00",
                   width=str(size),
                   height=str(size),
                   tooltip=a
                   )
            pos[0] += SIZE_AUTHOR

    def get_tooltip(self, key):
        j = self.all_articles[key]
        return j["title"] + "&#10;Year: " + j["year"] + "&#10;Cits: " + str(j["num_citations"]) + "&#10;Authors: " + j["authors"]

    def add_first_layer_nodes(self, g, pos):
        for key in [x.encode('utf-8') for x in sort_articles(self.articles1L)]:
            s = str(self.get_size_of_art(key)) + '!'
            g.node(key,
                   group='1L',
                   fixedsize='true',
                   width=s,
                   # nodesep=str(SIZE_MAX),
                   height=s,
                   # pos=str_(pos),
                   style="filled",
                   fillcolor=self.get_color_of_node(key),
                   color='black',
                   URL=cgi.escape(
                       self.articles1L[key]['url'].replace('http://scholar.google.com/', '')),

                   tooltip=self.get_tooltip(key))
            pos[0], pos[1] = pos[0]+SIZE_MAX, pos[1]  # - 5

    def add_second_layer_nodes(self, g, pos):
        for key in [x.encode('utf-8') for x in sort_articles(self.articles2L)]:
            s = str(self.get_size_of_art(key)) + '!'
            g.node(key,
                   group='2L',
                   width=s,
                   height=s,
                   # pos=str_(pos),
                   style="filled",
                   fillcolor=self.get_color_of_node(key),
                   color='black',
                   URL=cgi.escape(
                       self.articles2L[key]['url'].replace('http://scholar.google.com/', '')),
                   tooltip=self.get_tooltip(key))

            pos[0], pos[1] = pos[0]+SIZE_MAX*4, pos[1]  # - 5*4

    def add_invis_auth_paths(self, g):
        start = self.authors[0]
        for index in self.authors[1:]:
            g.edge(start, index, minlen=str(0), weight='50', style='invis')
            start = index

    def add_invis_art_paths(self, g):
        layers = []
        for y in range(MIN_YEAR_LAYERS, self.MAX_YEAR+1):
            if y == MIN_YEAR_LAYERS:
                arts = get_before_and_in_year(
                    y, self.all_articles, self.MIN_YEAR)
            else:
                arts = get_in_year(y, self.all_articles)
            r = sort_articles(arts)
            for i in range(len(r)-1):
                g.edge(r[i],
                       r[i+1],
                       minlen=str(0),
                       weight='150',
                       constraint='true',
                       style='invis')
            layers.append(r) if len(r) > 0 else None

        layers = [self.authors[:len(self.authors)/2]] + layers
        for i_l in range(len(layers)-1):
            self.add_invis_list_to_list_paths(g, layers[i_l], layers[i_l+1])

    def add_invis_list_to_list_paths(self, g, l1, l2):
        r = int(abs((len(l1) - len(l2)) / 2.0))
        offset_l1 = 0
        offset_l2 = 0
        min_l = min(len(l1), len(l2))
        if len(l1) == min_l:
            offset_l2 = r
        else:
            offset_l1 = r

        for index in range(min_l):
            g.edge(l1[index+offset_l1],
                   l2[index + offset_l2],
                   maxlen=str(0),
                   weight='150',
                   constraint='true',
                   style='invis')

    def add_auth_paths(self, g):
        for key, value in self.all_articles.iteritems():
            for author in [author for author in value['authors_list'] if author in self.authors]:
                g.edge(author, key,
                       color="#00ff00",
                       constraint="true",
                       # minlen=str(SIZE_MAX),
                       weight='0'
                       )

    def add_cit_paths(self, g, nodes, color, archs):
        all_articles_keys = self.all_articles.keys()
        for key, value in nodes.iteritems():
            for dest in self.all_articles[key]['cited_by']:
                if dest in all_articles_keys:
                    archs = archs | set([key + '->' + dest])
                    g.edge(key,
                           dest,
                           color=color,
                           style='bold',
                           constraint='false')
                    # minlen=str(20),
                    # weight='0')  # 2f
        return archs

    def generate_graph(self):
        self.MAX_CIT_NUM = get_max_cit_num(self.all_articles)
        self.MIN_YEAR, self.MAX_YEAR = get_min_and_max_year(self.all_articles)
        self.MAX_CIT_RATIO = self.MAX_CIT_NUM/(self.MAX_YEAR - self.MIN_YEAR)
        self.MAX_CITS_AUTH = max_author_citations(
            self.authors, self.all_articles)
        self.color_range = color_range(self.MAX_YEAR+1 - self.MIN_YEAR)
        # , overlap='scale') # Digraph('deep_learning - SoA')

        f = Digraph(format='pdf', engine='dot', graph_attr=self.style['graph'])

        pos = [0, 0]
        self.add_authors_nodes(f, pos)

        pos = [0, -SIZE_MAX*10]
        self.add_first_layer_nodes(f, pos)

        pos = [pos[0]+50, pos[1] + SIZE_MAX*30]
        self.add_second_layer_nodes(f, pos)

        self.add_invis_auth_paths(f)
        self.add_invis_art_paths(f)

        cits = set([])

        self.add_auth_paths(f)
        cits = self.add_cit_paths(f, self.articles1L, "#0000a0", cits)
        cits = self.add_cit_paths(f, self.articles2L, "#C11B17", cits)
        cits = self.add_cit_paths(f, self.articles3L, "#FF00FF", cits)

        self.export_graph(f, EXPORT_ATTRS)

    def export_graph(self, g, attrs):
        for a in attrs:
            print 'writing ' + a[0]
            g.format = a[1]
            g.render(a[0], view=a[2])


def load_dict(f):
    d = build_res_dict(import_json(f))
    #d = get_most_pertinent('deep learning', d)
    d = get_most_cited(MIN_CITATIONS, d)
    d = get_min_year(MIN_YEAR, d)
    print 'dict ' + f + 'loaded'
    return d


def main():
    g = Grapher()
    g.all_articles = merge_results_lists()
    g.add_first_layer_articles(load_dict('results/FIRST LAYER.json'))
    g.add_second_layer_articles(load_dict('results/SECOND LAYER.json'))
    g.add_third_layer_articles(load_dict('results/THIRD LAYER.json'))
    r = {}
    k1 = g.articles1L.keys()
    k2 = g.articles2L.keys()
    k3 = g.articles3L.keys()
    for key in g.all_articles.keys():
        if key in k1 or key in k2 or key in k3:
            r[key] = g.all_articles[key]
    g.all_articles = r
    g.add_authors(get_all_authors(g.all_articles))
    g.generate_graph()


if __name__ == '__main__':
    main()
