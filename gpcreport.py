# Copyright (c) 2015, Qiurui He
# Department of Engineering, University of Cambridge

import numpy as np
import pylatex as pl
import pylatex.utils as ut
import os

class GPCReport(object):
    """
    AutoGPC data analysis report.
    """

    def __init__(self, root='./latex', paper='a4paper', history=None):
        self.root = root
        self.doc = pl.Document()

        self.makePreamble(paper=paper)
        self.makeDataSummary(kern=history[1]) # Note: history[0] is NoneKernel

    def makePreamble(self, paper='a4paper'):
        doc = self.doc

        doc.packages.append(pl.Package('geometry', options=['a4paper', 'margin=1.5in']))
        doc.packages.append(pl.Package('hyperref'))

        doc.preamble.append(pl.Command('title', 'AutoGPC Data Analysis Report'))
        doc.preamble.append(pl.Command('author', 'Automatic Statistician'))
        doc.preamble.append(pl.Command('date', ut.NoEscape(r'\today')))
        doc.append(ut.NoEscape(r'\maketitle'))

        doc.append(r'This report is automatically generated by the AutoGPC. For more information, please visit ')
        doc.append(pl.Command('url', 'https://github.com/charles92/autogpc'))
        doc.append(r'.')

    def makeDataSummary(self, kern=None):
        doc = self.doc
        data = kern.data
        dataShape = data.getDataShape()

        imgName = 'data'
        imgFormat = '.eps' if data.getDim() != 3 else '.png'
        imgOutName = imgName + imgFormat
        kern.draw(os.path.join(self.root, imgName), draw_kernel=False)

        with doc.create(pl.Section('The Data Set')):
            s = r'The training data set contains {0} data points'.format(data.getNum())
            s = s + r' which span {0} dimensions. '.format(data.getDim())
            for dim in xrange(data.getDim()):
                s = s + r"In dimension ``{0}'', ".format(data.XLabel[dim])
                s = s + r'the data has a minimum of {0:.2f} '.format(dataShape['x_min'][dim])
                s = s + r'and a maximum of {0:.2f}; '.format(dataShape['x_max'][dim])
                s = s + r'the standard deviation is {0:.2f}.'.format(dataShape['x_sd'][dim])

            doc.append(ut.NoEscape(s))

            with doc.create(pl.Figure(position='h!')) as fig:
                fig.add_image(imgOutName)
                fig.add_caption(r'The input data set.')

    def export(self, filename=None):
        if filename is None:
            filename = 'report'
        self.doc.generate_pdf(os.path.join(self.root, filename))
