# Copyright (c) 2015, Qiurui He
# Department of Engineering, University of Cambridge

import numpy as np
import pylatex as pl
import pylatex.utils as ut
import os, shutil
from gpckernel import GPCKernel
from gpcdata import GPCData

class GPCReport(object):
    """
    AutoGPC data analysis report.
    """

    def __init__(self, root='./latex', name='default', paper='a4paper', history=None, best1d=None, constkernel=None):
        self.name = name
        self.history = history
        self.best1d = best1d
        self.constker = constkernel
        self.kers, self.cums = cumulateAdditiveKernels(history[-1].toSummands())

        # Prepare directory
        p = os.path.join(root, name)
        try:
            if os.path.exists(p): shutil.rmtree(p)
            os.makedirs(p)
        except Exception as e:
            print e
        self.path = p

        # Figure numbering
        self.fignum = 1

        # Make document
        self.doc = pl.Document()
        self.makePreamble(paper=paper)
        self.makeDataSummary()
        self.describeVariables()
        self.describeAdditiveComponents()


    def makePreamble(self, paper='a4paper'):
        doc = self.doc

        doc.packages.append(pl.Package('geometry', options=['a4paper', 'margin=1.2in']))
        doc.packages.append(pl.Package('hyperref'))
        doc.packages.append(pl.Package('babel', options=['UKenglish']))
        doc.packages.append(pl.Package('isodate', options=['UKenglish']))

        title_str = r'AutoGPC Data Analysis Report on ' + self.name + ' Dataset'
        doc.preamble.append(pl.Command('title', ut.NoEscape(title_str)))
        doc.preamble.append(pl.Command('author', 'Automatic Statistician'))
        doc.preamble.append(pl.Command('date', ut.NoEscape(r'\today')))
        doc.append(ut.NoEscape(r'\maketitle'))

        s = "This report is automatically generated by the AutoGPC. " \
          + "AutoGPC is an automatic Gaussian Process (GP) classifier that " \
          + "aims to find the structure underlying a dataset without human input. " \
          + "For more information, please visit " \
          + r"\url{https://github.com/charles92/autogpc}."
        doc.append(ut.NoEscape(s))


    def makeDataSummary(self):
        kern = self.history[1]
        doc = self.doc
        data = kern.data
        dataShape = data.getDataShape()

        npts = data.getNum()
        ndim = data.getDim()
        npos = data.getClass(1).shape[0]
        nneg = data.getClass(0).shape[0]

        imgName = 'data'
        imgFormat = '.eps' if ndim != 3 else '.png'
        imgOutName = imgName + imgFormat
        kern.draw(os.path.join(self.path, imgName), draw_posterior=False)

        with doc.create(pl.Section("The Dataset")):
            s = "The training dataset spans {0} input dimensions, which are: ".format(ndim)
            doc.append(ut.NoEscape(s))
            with doc.create(pl.Enumerate()) as enum:
                for i in range(ndim):
                    enum.add_item(ut.NoEscape(dims2text([i], data, cap=True)))

            s = r"There is one binary output variable $y$: "
            doc.append(ut.NoEscape(s))
            with doc.create(pl.Itemize()) as itemize:
                s = r"$y=0$ (negative) represents ``{0}''".format(data.YLabel[0])
                itemize.add_item(ut.NoEscape(s))
                s = r"$y=1$ (positive) represents ``{0}''".format(data.YLabel[1])
                itemize.add_item(ut.NoEscape(s))

            s = "The training dataset contains {0} data points. ".format(npts) \
              + r"Among them, {0} ({1:.2f}\%) have positive class labels, ".format(npos, npos / float(npts) * 100) \
              + r"whereas other {0} ({1:.2f}\%) have negative labels. ".format(nneg, nneg / float(npts) * 100) \
              + "All input dimensions as well as the class label assignments " \
              + "are plotted in Figure {0}. ".format(self.fignum)
            doc.append(ut.NoEscape(s))

            with doc.create(pl.Figure(position='h!')) as fig:
                fig.add_image(imgOutName)
                s = "The input dataset. " \
                  + r"Positive samples (``{0}'') are coloured red, ".format(data.YLabel[1]) \
                  + r"and negative ones (``{0}'') blue. ".format(data.YLabel[0])
                fig.add_caption(ut.NoEscape(s))
                self.fignum += 1


    def describeOneVariable(self, ker):
        """
        Generate a subsection describing a particular variable.

        :param ker:
        :type ker:
        """
        assert isinstance(ker, GPCKernel), 'Argument must be of type GPCKernel'
        assert len(ker.getActiveDims()) == 1, 'The kernel must be one-dimensional'

        dim = ker.getActiveDims()[0]
        data = ker.data
        ds = data.getDataShape()

        xmu, xsd, xmin, xmax = ds['x_mu'][dim], ds['x_sd'][dim], ds['x_min'][dim], ds['x_max'][dim]
        error = ker.error()
        mon = ker.monotonicity()
        per = ker.period()

        doc = self.doc
        with doc.create(pl.Subsection(ut.NoEscape(dims2text([dim], data, cap=True)))):
            s = dims2text([dim], data, cap=True) + " has " \
              + "mean value {0:.2f} and standard deviation {1:.2f}. ".format(xmu, xsd) \
              + "Its observed minimum and maximum are {0:.2f} and {1:.2f} respectively. ".format(xmin, xmax) \
              + "A GP classifier trained on this variable alone can achieve " \
              + r"a cross-validated training error of {0:.2f}\%. ".format(error * 100)
            if mon != 0:
                corr_str = "positive" if mon > 0 else "negative"
                s = s + "There is a " + corr_str + " correlation between the value " \
                      + "of this variable and the likelihood of the sample being " \
                      + "classified as positive. "
            elif per != 0:
                s = s + "The class assignment is approximately periodic with " \
                      + dims2text([dim], data) + ". " \
                      + "The period is about {0:.2f}. ".format(per)
            else:
                s = s + "No monotonicity or periodicity is associated with this variable. "
            s = s + "The GP posterior trained on this variable is plotted in Figure {0}. ".format(self.fignum)
            doc.append(ut.NoEscape(s))

            # Plotting
            imgName = 'var{0}'.format(dim)
            imgFormat = '.eps'
            imgFilename = imgName + imgFormat
            ker.draw(os.path.join(self.path, imgName), active_dims_only=True)
            caption_str = r"Trained classifier on " + dims2text([dim], ker.data) + "."
            with doc.create(pl.Figure(position='h!')) as fig:
                fig.add_image(imgFilename, width=ut.NoEscape(r'0.5\textwidth'))
                fig.add_caption(ut.NoEscape(caption_str))
                self.fignum += 1


    def tabulateVariables(self):
        """
        Create a table that summarises all input variables.
        """
        ks = self.best1d[:]
        ks.append(self.constker)
        ks.sort(key=lambda k: k.error())
        data = ks[0].data
        ds = data.getDataShape()

        nlml_min_k = min(ks, key=lambda k: k.getNLML())
        error_min_k = min(ks, key=lambda k: k.error())

        doc = self.doc
        with doc.create(pl.Table(position='h!')) as tab:
            tab.add_caption(ut.NoEscape("Input variables"))

            t = pl.Tabular('rl|rrr|crr')
            t.add_hline()
            t.add_hline()
            t.add_row((
                pl.MultiColumn(1, align='c', data=''),
                pl.MultiColumn(1, align='c|', data=ut.bold('Variable')),
                pl.MultiColumn(1, align='c', data=ut.bold('Min')),
                pl.MultiColumn(1, align='c', data=ut.bold('Max')),
                pl.MultiColumn(1, align='c|', data=ut.bold('Mean')),
                pl.MultiColumn(1, align='c', data=ut.bold('Kernel')),
                pl.MultiColumn(1, align='c', data=ut.bold('NLML')),
                pl.MultiColumn(1, align='c', data=ut.bold('Error')) ))
            t.add_hline()

            for k in ks:
                if k is self.constker:
                    row = [
                        ut.italic('--', escape=False),
                        ut.italic('Baseline', escape=False),
                        ut.italic('--', escape=False),
                        ut.italic('--', escape=False),
                        ut.italic('--', escape=False),
                        ut.italic(k.shortInterp(), escape=False),
                        ut.italic('{0:.2f}'.format(k.getNLML()), escape=False),
                        ut.italic(r'{0:.2f}\%'.format(k.error()*100), escape=False) ]
                else:
                    dim = k.getActiveDims()[0]
                    row = [
                        dim+1,
                        data.XLabel[dim],
                        '{0:.2f}'.format(ds['x_min'][dim]),
                        '{0:.2f}'.format(ds['x_max'][dim]),
                        '{0:.2f}'.format(ds['x_mu'][dim]),
                        k.shortInterp(),
                        ut.NoEscape('{0:.2f}'.format(k.getNLML())),
                        ut.NoEscape(r'{0:.2f}\%'.format(k.error()*100)) ]
                if k is nlml_min_k:
                    row[6] = ut.bold(row[6])
                if k is error_min_k:
                    row[7] = ut.bold(row[7])

                t.add_row(tuple(row))

            t.add_hline()

            tab.append(ut.NoEscape(r'\centering'))
            tab.append(t)


    def describeVariables(self):
        """
        Generate a section describing all input dimensions / variables.
        """
        n_terms = len(self.best1d)
        doc = self.doc
        with doc.create(pl.Section("Individual Variable Analysis")):
            s = "First, we try to classify the training samples using only one " \
              + "of the {0:d} input dimensions. ".format(n_terms) \
              + "By considering the best classification performance that is " \
              + "achievable in each dimension, we are able to infer which " \
              + "dimensions are the most relevant to the class assignment. "
            doc.append(ut.NoEscape(s))
            doc.append("\n\n")

            s = "Listed below in Table 1 are all input variables involved, " \
              + "in descending order of inferred relevance " \
              + "(i.e. in ascending order of cross-validated training error of " \
              + "the best one-dimensional GP classifier). " \
              + "The baseline performance is also included, which is achieved " \
              + "with a constant GP kernel. The effect of the baseline classifier " \
              + "is to indiscriminately classify all samples as either positive " \
              + "or negative, whichever is more frequent in the training data. "
            doc.append(ut.NoEscape(s))

            self.tabulateVariables()

            for i in range(n_terms):
                self.describeOneVariable(self.best1d[i])


    def describeOneAdditiveComponent(self, term):
        """
        Generate a subsection that describes one additive component.

        :param term: term to be analysed
        :type term: integer
        """
        ker, cum = self.kers[term - 1], self.cums[term - 1]
        data = ker.data
        kdims = ker.getActiveDims()
        error = cum.error()
        if term > 1: delta = self.cums[term - 2].error() - error
        nlml = cum.getNLML()

        doc = self.doc
        with doc.create(pl.Subsection("Component {0}".format(term))):
            if term == 1:
                s = r"With only one additive component, the GP classifier can achieve " \
                  + r"a cross-validated training error rate of {0:.2f}\%. ".format(error * 100) \
                  + r"The corresponding negative log marginal likelihood is {0:.2f}. ".format(nlml)
                doc.append(ut.NoEscape(s))

                s = r"This component operates on " + dims2text(kdims, data) + ", " \
                  + r"as shown in Figure {0}. ".format(self.fignum)
                doc.append(ut.NoEscape(s))

            else:
                s = r"With {0} additive components, the cross-validated training error ".format(term) \
                  + r"can be reduced by {0:.2f}\% to {1:.2f}\%. ".format(delta * 100, error * 100) \
                  + r"The corresponding negative log marginal likelihood is {0:.2f}. ".format(nlml)
                doc.append(ut.NoEscape(s))

                s = r"The additional component operates on " + dims2text(kdims, data) + ", " \
                  + r"as shown in Figure {0}. ".format(self.fignum)
                doc.append(ut.NoEscape(s))

            self.makeInteractionFigure(ker, cum, term)


    def describeAdditiveComponents(self):
        """
        Generate a section describing all additive components present.
        """
        n_terms = len(self.kers)
        error = self.cums[-1].error()
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
        assert isinstance(ker, GPCKernel), 'Kernel must be of type GPCKernel'
        assert isinstance(cum, GPCKernel), 'Kernel must be of type GPCKernel'

        doc = self.doc
        kerDims = ker.getActiveDims()
        cumDims = cum.getActiveDims()

        img1Name = 'additive{0}ker'.format(n_terms)
        img1Format = '.eps' if len(kerDims) != 3 else '.png'
        img1Filename = img1Name + img1Format
        ker.draw(os.path.join(self.path, img1Name), active_dims_only=True)

        if n_terms == 1 or len(cumDims) > 3:
            # Only present current additive component
            caption_str = r"Trained classifier on " + dims2text(kerDims, ker.data) + "."
            with doc.create(pl.Figure(position='h!')) as fig:
                fig.add_image(img1Filename, width=ut.NoEscape(r'0.5\textwidth'))
                fig.add_caption(ut.NoEscape(caption_str))
                self.fignum += 1

        else:
            # Present both current component and cumulative kernel
            img2Name = 'additive{0}cum'.format(n_terms)
            img2Format = '.eps' if len(cumDims) != 3 else '.png'
            img2Filename = img2Name + img2Format
            cum.draw(os.path.join(self.path, img2Name), active_dims_only=True)
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
                self.fignum += 1


    def export(self, filename=None):
        if filename is None:
            filename = 'report'
        self.doc.generate_pdf(os.path.join(self.path, filename))


##############################################
#                                            #
#             Helper Functions               #
#                                            #
##############################################

def dims2text(dims, data, cap=False):
    """
    Convert a list of dimensions to their names.

    :param dims: list of dimensions (i.e. integers)
    :param data: `GPCData` object
    :param cap: captitalise first letter if True (default to False)
    :type cap: boolean
    """
    assert len(dims) > 0, 'The list of dimensions must contain at least one member.'

    xl = data.XLabel
    text = "Variable" if cap else "variable"
    if len(dims) == 1:
        text = text + " ``{0}''".format(xl[dims[0]])
    else:
        text = text + "s "
        for i in range(len(dims) - 2):
            text = text + "``{0}'', ".format(xl[dims[i]])
        text = text + r"``{0}'' and ``{1}''".format(xl[dims[-2]],xl[dims[-1]])

    return text


def cumulateAdditiveKernels(summands):
    """
    Incrementally cumulate additive components of a kernel, producing the full
    kernel in the end.

    :param summands: list of GPCKernel objects to be cumulated
    """
    # Sort in descending order of cross-validated training error
    terms = sorted(summands, key=lambda k: k.error(), reverse=True)
    ker = terms.pop()
    cum = ker
    kers = [ker]
    cums = [cum]

    # Progressively include more additive components according to the cross-
    # validated training error of the cumulated additive kernel
    while len(terms) > 0:
        terms = sorted(terms, key=lambda k: cum.add(k).error(), reverse=True)
        ker = terms.pop()
        cum = cum.add(ker)
        kers.append(ker)
        cums.append(cum)

    return kers, cums
