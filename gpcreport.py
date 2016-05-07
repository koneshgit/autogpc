# Copyright (c) 2015, Qiurui He
# Department of Engineering, University of Cambridge

import numpy as np
import pylatex as pl
import pylatex.utils as ut
import os
from gpckernel import GPCKernel
from gpckernel import cumulateAdditiveKernels

class GPCReport(object):
    """
    AutoGPC data analysis report.
    """

    def __init__(self, root='./latex', paper='a4paper', history=None):
        self.root = root
        self.doc = pl.Document()
        self.history = history

        summands = self.history[-1].toSummands()
        self.kers, self.cums = cumulateAdditiveKernels(summands)

        self.makePreamble(paper=paper)
        self.describeAdditiveComponents()


    def makePreamble(self, paper='a4paper'):
        doc = self.doc

        doc.packages.append(pl.Package('geometry', options=['a4paper', 'margin=1.2in']))
        doc.packages.append(pl.Package('hyperref'))
        doc.packages.append(pl.Package('babel', options=['UKenglish']))
        doc.packages.append(pl.Package('isodate', options=['UKenglish']))

        doc.preamble.append(pl.Command('title', 'AutoGPC Data Analysis Report'))
        doc.preamble.append(pl.Command('author', 'Automatic Statistician'))
        doc.preamble.append(pl.Command('date', ut.NoEscape(r'\today')))
        doc.append(ut.NoEscape(r'\maketitle'))

        doc.append(r'This report is automatically generated by the AutoGPC. For more information, please visit ')
        doc.append(pl.Command('url', 'https://github.com/charles92/autogpc'))


    def makeDataSummary(self, search_history=None):
        assert isinstance(search_history, list) and len(search_history) > 1, \
            'search_history must be a list containing >=2 GPCKernel instances'
        kern = search_history[1]
        doc = self.doc
        data = kern.data
        dataShape = data.getDataShape()

        imgName = 'data'
        imgFormat = '.eps' if data.getDim() != 3 else '.png'
        imgOutName = imgName + imgFormat
        kern.draw(os.path.join(self.root, imgName), draw_posterior=False)

        with doc.create(pl.Section("The Dataset")):
            s = r"The training dataset contains {0} data points".format(data.getNum())
            s = s + r" which span {0} dimensions. ".format(data.getDim())
            for dim in xrange(data.getDim()):
                s = s + r"In dimension ``{0}'', ".format(data.XLabel[dim])
                s = s + r"the data has a minimum of {0:.2f} ".format(dataShape['x_min'][dim])
                s = s + r"and a maximum of {0:.2f}; ".format(dataShape['x_max'][dim])
                s = s + r"the standard deviation is {0:.2f}. ".format(dataShape['x_sd'][dim])

            doc.append(ut.NoEscape(s))

            with doc.create(pl.Figure(position='h!')) as fig:
                fig.add_image(imgOutName)
                fig.add_caption(r"The input dataset.")


    def describeOneAdditiveComponent(self, term):
        """
        Generate a subsection that describes one additive component.

        :param term: term to be analysed
        :type term: integer
        """
        ker, cum = self.kers[term - 1], self.cums[term - 1]
        data = ker.data
        kdims = ker.getActiveDims()
        error = cum.getCvError()
        if term > 1: delta = self.cums[term - 2].getCvError() - error
        nlml = cum.getNLML()

        doc = self.doc
        with doc.create(pl.Subsection("Component {0}".format(term))):
            if term == 1:
                s = r"With only one additive component, the GP classifier can achieve " \
                  + r"a cross-validated training error rate of {0:.2f}\%. ".format(error * 100) \
                  + r"The corresponding negative log marginal likelihood is {0:.2f}. ".format(nlml)
                doc.append(ut.NoEscape(s))

                s = r"This component operates on " + dims2text(kdims, data) + ", " \
                  + r"as shown in the figure below. "
                doc.append(ut.NoEscape(s))

            else:
                s = r"With {0} additive components, the cross-validated training error ".format(term) \
                  + r"can be reduced by {0:.2f}\% to {1:.2f}\%. ".format(delta * 100, error * 100) \
                  + r"The corresponding negative log marginal likelihood is {0:.2f}. ".format(nlml)
                doc.append(ut.NoEscape(s))

                s = r"The additional component operates on " + dims2text(kdims, data) + ", " \
                  + r"as shown in the figure below. "
                doc.append(ut.NoEscape(s))

            self.makeInteractionFigure(ker, cum, term)


    def describeAdditiveComponents(self):
        """
        Generate a section describing all additive components present.
        """
        n_terms = len(self.kers)
        error = self.cums[-1].getCvError()
        doc = self.doc
        with doc.create(pl.Section("Additive Component Analysis")):
            s = r"The pattern underlying the dataset can be decomposed into " \
              + r"{0} additive components, ".format(n_terms) \
              + r"which contribute jointly to the final classifier which we have trained. " \
              + r"With all components in action, the classifier can achieve " \
              + r"a cross-validated training error rate of {0:.2f}\%. ".format(error * 100) \
              + r"The performance cannot be further improved by adding more components. "
            doc.append(ut.NoEscape(s))
            for i in range(1, n_terms + 1):
                self.describeOneAdditiveComponent(i)


    def makeInteractionFigure(self, ker, cum, n_terms):
        """
        Create figure for interaction analysis, which includes a subfigure of
        the latest additive component and a subfigure of posterior of the overall
        compositional kernel up to now.

        :param ker: latest additive component to be plotted
        :type ker: GPCKernel
        :param cum: overall compositional kernel up to and including `ker`
        :type cum: GPCKernel
        :param n_terms: number of additive terms considered in `cum` so far
        """
        assert isinstance(ker, GPCKernel)
        assert isinstance(cum, GPCKernel)

        doc = self.doc
        kerDims = ker.getActiveDims()
        cumDims = cum.getActiveDims()

        img1Name = 'additiveterm{0}ker'.format(n_terms)
        img1Format = '.eps' if len(kerDims) != 3 else '.png'
        img1Filename = img1Name + img1Format
        ker.draw(os.path.join(self.root, img1Name), active_dims_only=True)

        if n_terms == 1 or len(cumDims) > 3:
            # Only present current additive component
            caption_str = r"Trained classifier on " + dims2text(kerDims, ker.data) + "."
            with doc.create(pl.Figure(position='h!')) as fig:
                fig.add_image(img1Filename, width=ut.NoEscape(r'0.5\textwidth'))
                fig.add_caption(ut.NoEscape(caption_str))

        else:
            # Present both current component and cumulative kernel
            img2Name = 'additiveterm{0}cum'.format(n_terms)
            img2Format = '.eps' if len(cumDims) != 3 else '.png'
            img2Filename = img2Name + img2Format
            cum.draw(os.path.join(self.root, img2Name), active_dims_only=True)
            caption1_str = r"Current additive component involving " + dims2text(kerDims, ker.data) + "."
            caption2_str = r"Previous and current components combined, involving " + dims2text(cumDims, cum.data) + "."
            caption_str = r"Trained classifier on " + dims2text(cumDims, cum.data) + "."

            with doc.create(pl.Figure(position='h!')) as fig:
                with doc.create(pl.SubFigure(
                    position='b',
                    width=ut.NoEscape(r'0.45\textwidth') )) as subfig1:
                    subfig1.add_image(img1Filename, width=ut.NoEscape(r'\textwidth'))
                    subfig1.add_caption(ut.NoEscape(caption1_str))
                doc.append(ut.NoEscape(r'\hfill'))
                with doc.create(pl.SubFigure(
                    position='b',
                    width=ut.NoEscape(r'0.45\textwidth') )) as subfig2:
                    subfig2.add_image(img2Filename, width=ut.NoEscape(r'\textwidth'))
                    subfig2.add_caption(ut.NoEscape(caption2_str))
                fig.add_caption(ut.NoEscape(caption_str))


    def export(self, filename=None):
        if filename is None:
            filename = 'report'
        self.doc.generate_pdf(os.path.join(self.root, filename))


##############################################
#                                            #
#             Helper Functions               #
#                                            #
##############################################

def dims2text(dims, data):
    """
    Convert a list of dimensions to their names

    :param dims: list of dimensions (i.e. integers)
    :param data: `GPCData` object
    """
    assert len(dims) > 0, 'The list of dimensions must contain at least one member.'

    xl = data.XLabel
    if len(dims) == 1:
        return r"variable ``{0}''".format(xl[dims[0]])
    else:
        text = "variables "
        for i in range(len(dims) - 2):
            text = text + r"``{0}'', ".format(xl[dims[i]])
        text = text + r"``{0}'' and ``{1}''".format(xl[dims[-2]],xl[dims[-1]])

    return text
