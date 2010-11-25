from pylab import *
import textwrap
from copy import deepcopy 
import traceback
from scipy.optimize import leastsq
from scipy.signal import fftconvolve
from inspect import getargspec
#rc('image',aspect='auto',interpolation='bilinear')
rc('image',aspect='auto',interpolation='nearest')
rcParams['xtick.direction'] = 'out'
rcParams['xtick.major.size'] = 12
rcParams['xtick.minor.size'] = 6
rcParams['ytick.direction'] = 'out'
rcParams['ytick.major.size'] = 12
rcParams['ytick.minor.size'] = 6
#rcParams['lines.linewidth'] = 3.0
rcParams['legend.fontsize'] = 12
rcParams['axes.grid'] = False
rcParams['font.size'] = 18
#{{{ function trickery
def mydiff(data,axis = -1):
    '''this will replace diff with a version that has the same number of indeces, with the last being the copy of the first'''
    newdata = zeros(shape(data),dtype = data.dtype)
    indeces = [slice(None,None,None)]*len(data.shape)
    indeces[axis] = slice(None,-1,None)
    newdata[indeces] = diff(data,axis = axis)
    #setfrom = list(indeces)
    #indeces[axis] = -1
    #setfrom[axis] = 0
    #newdata[indeces] = newdata[setfrom]
    return newdata
#}}}
def emptyfunction():
    pass
#{{{ errors
class CustomError(Exception):
    def __init__(self, *value):
        if len(value)>1:
            retval = map(str,value)
        else:
            retval = str(value)
        retval = map(str,value)
        retval = ' '.join(retval)
        retval = '\n'+'\n'.join(textwrap.wrap(retval,90))
        if traceback.format_exc() != 'None':
            retval += '\n\nOriginal Traceback:\n'+''.join(['V']*40)+'\n'+traceback.format_exc() + '\n' + ''.join(['^']*40) + '\n'
        Exception.__init__(self,retval)
        return
def copy_maybe_none(input):
    if input == None:
        return None
    else:
        if type(input) is list:
            return map(copy,input)
        else:
            return input.copy()
def maprep(*mylist):
    mylist = list(mylist)
    for j in range(0,len(mylist)):
        if type(mylist[j]) is not str:
            mylist[j] = mylist[j].__repr__()
    return ' '.join(mylist)
#}}}
#{{{ indeces to slice
#}}}
#{{{ add slashes for dir's
def dirformat(file):
        #{{{ format strings
        if file[-1]!='/':
            file += '/'
        #}}}
        return file
#}}}
#{{{ old grid and tick
def gridandtick(ax,rotation=(0,0),precision=(2,2),labelstring=('',''),gridcolor=r_[0,0,0],formatonly = False,fixed_y_locator = None,logarithmic = False,use_grid = True):
    if not formatonly:
        #{{{x ticks
        # determine the size
        width = abs(diff(ax.get_xlim()))
        if width==0:
            raise CustomError('x axis width is zero')
        widthexp = floor(log(width)/log(10.))-1
        scalefactor = 10**widthexp
        width /= scalefactor
        majorLocator = MultipleLocator(5*scalefactor)
        #majorFormatter = FormatStrFormatter('%0.'+'%d'%precision[0]+'f'+labelstring[0])# labelstring can be used, for instance, for pi
        #ax.xaxis.set_major_formatter(majorFormatter)
        minorLocator   = MultipleLocator(1*scalefactor)
        ax.xaxis.set_major_locator(majorLocator)
        #for the minor ticks, use no labels; default NullFormatter
        ax.xaxis.set_minor_locator(minorLocator)
        #}}}
        #{{{ y ticks
        width = abs(diff(ax.get_ylim()))
        if width==0:
            raise CustomError('y axis width is zero')
        widthexp = floor(log(width)/log(10.))-1
        scalefactor = 10**widthexp
        width /= scalefactor
        if fixed_y_locator == None:
            if logarithmic:
                majorLocator = LogLocator(10)
            else:
                majorLocator   = MultipleLocator(5*scalefactor)
        else:
            majorLocator   = MultipleLocator(fixed_y_locator[4::5])
        #majorFormatter = FormatStrFormatter('%0.'+'%d'%precision[1]+'f'+labelstring[1])# labelstring can be used, for instance, for pi
        #ax.yaxis.set_major_formatter(majorFormatter)
        if fixed_y_locator == None:
            if logarithmic:
                minorLocator = LogLocator(10,subs=r_[0:11])
            else:
                minorLocator   = MultipleLocator(1*scalefactor)
        else:
            minorLocator   = FixedLocator(fixed_y_locator)
        ax.yaxis.set_major_locator(majorLocator)
        #for the minor ticks, use no labels; default NullFormatter
        ax.yaxis.set_minor_locator(minorLocator)
        #}}}
    grid(use_grid,which='major',color=gridcolor,alpha=0.4,linestyle='-')
    grid(use_grid,which='minor',color=gridcolor,alpha=0.2,linestyle='-')
    labels = ax.get_xticklabels()
    setp(labels,rotation=rotation[0],fontsize=10)
    labels = ax.get_yticklabels()
    setp(labels,rotation=rotation[1],fontsize=10)
    fig = gcf()
    fig.autofmt_xdate()
def gridon(gridcolor=r_[0,0,0]):
    grid(True,which='major',color=gridcolor,alpha=0.4,linestyle='-')
    grid(True,which='minor',color=gridcolor,alpha=0.2,linestyle='-')
#}}}
#{{{ a better version?
def othergridandtick(ax,rotation=(0,0),precision=(2,2),labelstring=('',''),gridcolor=r_[0,0,0]):
    #{{{x ticks
    # determine the size
    ax.xaxis.set_major_locator(MaxNLocator(10)) # could use multiplelocator if it keeps try to do multiples of 2
    ax.xaxis.set_minor_locator(MaxNLocator(50))
    #}}}
    #{{{ y ticks
    ax.yaxis.set_major_locator(MaxNLocator(10))
    ax.yaxis.set_minor_locator(MaxNLocator(50))
    #}}}
    grid(True,which='major',color=gridcolor,alpha=0.4,linestyle='-')
    grid(True,which='minor',color=gridcolor,alpha=0.2,linestyle='-')
    labels = ax.get_xticklabels()
    setp(labels,rotation=rotation[0],fontsize=10)
    labels = ax.get_yticklabels()
    setp(labels,rotation=rotation[1],fontsize=10)
#}}}
#{{{ plot wrapper
global OLDplot
OLDplot = plot
global myplotfunc
myplotfunc = OLDplot
def whereblocks(a): # returns contiguous chunks where the condition is true
    parselist = where(a)[0]
    jumps_at = where(diff(parselist)>1)[0]+1
    retlist = []
    lastjump = 0
    for jump in jumps_at:
        retlist += [parselist[lastjump:jump]]
        lastjump = jump
    retlist += [parselist[lastjump:]]
    return retlist
def autolegend(*args):
    #lg = legend(legendstr,'best'),loc = 2, borderaxespad = 0.)
    if len(args)==0:
        lg = legend(loc='best')
    elif len(args)==1:
        lg = legend(args[0],'best')
    else:
        lg = legend(args[0],args[1],'best')
    lg.get_frame().set_alpha(0.45)
    return lg
def plot_color_counter(*args):
        ax = gca()
        if len(args)>0:
            ax._get_lines.count = args[0] # set the value of the color counter
        return ax._get_lines.count
def nextfigure(figurelist,name):
        figure(len(figurelist)+1)
        figurelist.append(name)
        return figurelist
def text_on_plot(x,y,thistext,**kwargs):
    ax = gca()
    newkwargs = {'transform':ax.transAxes,'size':'x-large',"horizontalalignment":'center'}
    if 'match_data' in kwargs.keys():
        if kwargs['match_data'].get_plot_color() is not None:
            newkwargs.update({'color':kwargs['match_data'].get_plot_color()})
        else:
            raise CustomError('You passed match_data to text_on_plot, but I can\'t find a color in the object')
    return text(x,y,thistext,**newkwargs)
def plot(*args,**kwargs):
    global myplotfunc
    myplotfunc = OLDplot # default
    #{{{ all possible properties
    myformat = None 
    myxlabel = None
    myylabel = None
    myx = None
    myy = None
    #}}}
    try:
        #{{{assign all the possible combinations
        if len(args)==1:
            myy = args[0]
        elif (len(args)==2) and (type(args[1]) is str):
            myy = args[0]
            myformat = args[1]
        else:
            myx = args[0]
            myy = args[1]
        if len(args)==3:
            myformat = args[2]
        if isscalar(myx):
            myx = array([myx])
        if isscalar(myy):
            myy = array([myy])
        #}}}
        #{{{ parse nddata
        if isinstance(myy,nddata):
            if myy.get_plot_color() is not None:
                kwargs.update({'color':myy.get_plot_color()})
            if (len(myy.dimlabels)>1):
                myylabel = myy.dimlabels[1]
            if (len(myy.dimlabels)>0):
                myxlabel = myy.dimlabels[0]
            if (myx == None):
                try:
                    if (len(myy.axis_coords)>0) and (len(myy.axis_coords[0])>0):
                        myx = myy.axis_coords[0]
                    else:
                        myx = None
                except:
                    raise CustomError("problem, ",shape(myy.axis_coords),"not valid axes for",ndshape(myy))
            if type(myy.data_error) is ndarray and len(myy.data_error)>0: #then this should be an errorbar plot
                myplotfunc = errorbar
                if myformat != None:
                    kwargs.update({'fmt':myformat})
                    myformat = None
                #{{{ pop any singleton dims
                myyerror = myy.get_error()
                myyerror = squeeze(myyerror.copy())
                #}}}
                kwargs.update({'yerr':myyerror})
                valueforxerr = myy.get_error(myy.dimlabels[0])
                if valueforxerr != None: # if we have x errorbars too
                    #print "DEBUG decided to assign to xerr:",valueforxerr
                    kwargs.update({'xerr':valueforxerr})

            myy = squeeze(myy.data.copy())
        #}}}
        #{{{ semilog where appropriate
        if (myx != None) and (len(myx)>1): # by doing this and making myplotfunc global, we preserve the plot style if we want to tack on one point
            b = diff(log10(myx))
            if (size(b)>3) and all(abs((b-b[0])/b[0])<1e-4) and not ('nosemilog' in kwargs.keys()):
                myplotfunc = semilogx
            if ('nosemilog' in kwargs.keys()):
                kwargs.pop('nosemilog')
        if 'plottype' in kwargs.keys():
            if kwargs['plottype'] == 'semilogy':
                myplotfunc = semilogy
            kwargs.pop('plottype')
        #}}}
        #{{{ hsv plots when we have multiple lines
        if len(shape(myy))>1:
            #{{{ hsv plots
            hold(True)
            retval = []
            for j in range(0,myy.shape[1]):
                #{{{ this is the way to assign plot arguments
                plotargs = [myx,myy[:,j],myformat]
                while None in plotargs:
                    plotargs.remove(None)
                #}}}
                #{{{ here, i update the kwargs to include the specific color for this line
                newkwargs = kwargs.copy() # kwargs is a dict
                newkwargs.update({'color':cm.hsv(double(j)/double(myy.shape[1]))})
                #}}}
                myy[isinf(myy)] = NaN # added this to prevent an overflow error
                try:
                    retval += [myplotfunc(*tuple(plotargs),**newkwargs)]
                    #print "\n\n\\begin{verbatim}DEBUG plot:",plotargs,'\nkwargs:\n',newkwargs,'\\end{verbatim}'
                except: 
                    #print "shape(yerr)",shape(newkwargs['yerr'])
                    raise CustomError("Error trying to plot using function",myplotfunc,len(plotargs),"arguments",plotargs,"of len",map(len,plotargs),"and",len(newkwargs),"options",newkwargs,"of len",map(len,newkwargs.values()))
            #hold(False)
            #}}}
            #}}}
        else:
            plotargs = [myx,myy,myformat]
            while None in plotargs:
                plotargs.remove(None)
            try:
                retval = myplotfunc(*tuple(plotargs),**kwargs)
            except:
                raise CustomError('error trying to plot',myplotfunc,'with arguments',plotargs,'and kwargs',kwargs,'\nsizes of arguments:',[shape(j) for j in plotargs])
        #{{{ attach labels and such
        if (myxlabel!=None):
            xlabel(myxlabel)
        if (myylabel!=None):
            ylabel(myylabel)
        axis('tight')
        #grid(True)
        #}}}
    except:
        message = 'Error plotting,'
        message += ':'
        raise CustomError(message,'myformat',myformat,
                'myxlabel',type(myxlabel),shape(myxlabel),
                'myylabel',type(myylabel),shape(myylabel),
                'myy',type(myy),shape(myy),
                'myx',type(myx),shape(myx))
    return retval
#}}}
#{{{general functions
def box_muller(length):
    r'''algorithm to generate normally distributed noise'''
    s1 = rand(length)
    s2 = rand(length)
    n1 = sqrt(-2*log(s1))*cos(2*pi*s2)
    n2 = sqrt(-2*log(s1))*sin(2*pi*s2)
    return (n1 + 1j * n2)*0.5
#}}}

#{{{nddata
#{{{ shaping and allocating
class ndshape ():
    def __init__(self,*args):
        if len(args) == 2:
            self.shape = list(args[0])
            self.dimlabels = args[1]
        if len(args) == 1: #assum that it's an nddata object
            self.shape = list(args[0].data.shape)
            self.dimlabels = list(args[0].dimlabels)
        return
    def __setitem__(self,reference,setto):
        self.shape[self.dimlabels.index(reference)] = setto
        return
    def copy(self):
        return deepcopy(self)
    def __add__(self,arg):
        shape = arg[0]
        dimlabels = arg[1]
        self.shape = shape + self.shape
        self.dimlabels = dimlabels + self.dimlabels
        return self
    def __repr__(self): #how it responds to print
        return zip(self.shape,self.dimlabels).__repr__()
    def __getitem__(self,args):
        try:
            mydict = dict(zip(self.dimlabels,self.shape))
        except:
            raise CustomError("either dimlabels=",self.dimlabels,"or shape",self.shape,"not in the correct format")
        return mydict[args]
    def pop(self,label):
        thisindex = self.dimlabels.index(label)
        self.dimlabels.pop(thisindex)
        self.shape.pop(thisindex)
    def alloc(self,dtype='complex128'):
        return nddata(zeros(tuple(self.shape),dtype=dtype),self.shape,self.dimlabels)
#}}}
#{{{ format out to a certain decimal place
def dp(number,decimalplaces,scientific=False):
    if scientific:
        tenlog = floor(log(number)/log(10.))
        number /= 10**tenlog
        fstring = '%0.'+'%d'%decimalplaces+r'f\times 10^{%d}'%tenlog
    else:
        fstring = '%0.'+'%d'%decimalplaces+'f'
    return fstring%number
#}}}
#{{{ concatenate datalist along dimname
def concat(datalist,dimname):
    #{{{ allocate a new datalist structure  
    t1size = 0
    #print 'DEBUG: type(datalist)',type(datalist)
    try:
        shapes = map(ndshape,datalist)
    except:
        if type(datalist) is not list:
            raise CustomError('You didn\'t pass a list, you passed a',type(datalist))
        raise CustomError('Problem with what you passed to concat, list of types,',map(type,datalist))
    for j in range(0,len(datalist)):
        if dimname in shapes[j].dimlabels:
            t1size += shapes[j][dimname]
            shapetocheck = list(shapes[j].shape)
            shapetocheck.pop(shapes[j].dimlabels.index(dimname))
        else:
            t1size += 1
            shapetocheck = list(shapes[j].shape)
        if j is 0:
            shapetocheckagainst = shapetocheck
        else:
            if any(~(array(shapetocheck) == array(shapetocheckagainst))):
                raise CustomError('For item ',j,'in concat, ',shapetocheck,'!=',shapetocheckagainst,'where all the shapes of the things you\'re trying to concat are:',shapes)
    newdatalist = ndshape(datalist[-1])
    if dimname in newdatalist.dimlabels:
        newdatalist[dimname] = t1size
    else:
        newdatalist += ([t1size],[dimname])
    #print "DEBUG newdatalist is shaped like",newdatalist
    newdatalist = newdatalist.alloc()
    #}}}
    #{{{ actually contact the datalist
    t1size = 0 # now use it to track to position
    for j in range(0,len(datalist)):
        if dimname in shapes[j].dimlabels:
            newdatalist[dimname,t1size:t1size+shapes[j][dimname]] = datalist[j]
            t1size += shapes[j][dimname]
        else:
            newdatalist[dimname,t1size:t1size+1] = datalist[j]
            t1size += 1
    #}}}
    #{{{ pull the axis labels from the last item in the list
    if len(datalist[-1].axis_coords)>0:
        dimlabels = list(datalist[-1].dimlabels)
        axis_coords = list(datalist[-1].axis_coords)
        #print "axis_coords are",axis_coords,"for",dimlabels
        if dimname in dimlabels:
            thisindex = dimlabels.index(dimname)
            dimlabels.pop(thisindex)
            axis_coords.pop(thisindex)
        dimlabels += [dimname]
        axis_coords += [r_[0:t1size]]
        try:
            newdatalist.labels(dimlabels,axis_coords)
        except:
            raise CustomError("trying to attach axes of lengths",map(len,axis_coords),"to",dimlabels)
    #}}}
    return newdatalist
#}}}
class nddata (object):
    want_to_prospa_decim_correct = False
    def __init__(self,data,sizes,dimlabels,axis_coords=[],ft_start_time = 0.,data_error = None, axis_coords_error = None,axis_coords_units = None, data_units = None, other_info = {}):
        if not (type(data) is ndarray):
            #if (type(data) is float64) or (type(data) is complex128) or (type(data) is list):
            if isscalar(data) or (type(data) is list) or (type(data) is tuple):
                data = array(data)
            else:
                raise CustomError('data is not an array, it\'s',type(data),'!')
        if not (type(dimlabels) is list):
            raise CustomError('labels are not a list')
        try:
            self.data = reshape(data,sizes)
        except:
            raise CustomError("trying to reshape a ",data.shape,"array with list of sizes",sizes)
        self.dimlabels = dimlabels
        self.axis_coords = axis_coords
        self.ft_start_time = ft_start_time
        self.data_error = data_error
        self.data_units = data_units
        self.other_info = dict(other_info)
        if axis_coords_error == None:
            self.axis_coords_error = [None]*len(axis_coords)
        else:
            self.axis_coords_error = axis_coords_error
        if axis_coords_units == None:
            self.axis_coords_units = [None]*len(axis_coords)
        else:
            self.axis_coords_units = axis_coords_units 
        return
    def __repr__(self):
        return repr(self.data)+'\n\t+/-'+repr(self.get_error())+'\ndimlabels=['+repr(self.dimlabels)+']\naxes='+repr(self.mkd(self.axis_coords))+'\n\t+/-'+repr(self.mkd(self.axis_coords_error))+'\n'
    def axn(self,axis):
        return self.dimlabels.index(axis)
    def mkd(self,*arg):
        if len(arg) == 1:
            #print 'DEBUG: mkd called on',arg[0]
            for i,v in enumerate(arg[0]):
                if type(v) == ndarray:
                    if v.shape == ():
                        arg[0][i] = None
            #print 'DEBUG: mkd fixed argument to',arg[0]
            return dict(zip(self.dimlabels,arg[0]))
        else:
            return dict(zip(self.dimlabels,[None]*len(self.dimlabels)))
    def fld(self,errordict):
        return [errordict[x] for x in self.dimlabels]
    #{{{ set + get the error
    def set_error(self,*args):
        r'''set the errors
either set_error('axisname',error_for_axis) or set_error(error_for_data)'''
        if (len(args) is 1) and (type(args[0]) is ndarray):
            self.data_error = reshape(args[0],shape(self.data))
        elif (len(args) is 2) and (type(args[0]) is str) and (type(args[1]) is nddata):
            self.axis_coords_error[self.axn(args[0])] = args[1]
        else:
            raise CustomError('Not a valid argument to set_error:',map(type,args))
        return self
    def random_mask(self,axisname,threshold = exp(-1.0),inversion = False):
        r'''generate a random mask with about 'threshold' of the points thrown out'''
        if inversion:
            threshold = threshold / (1.0 - threshold)
        myr = rand(self.data.shape[self.axn(axisname)]) # random array same length as the axis
        return myr > threshold
    def get_error(self,*args):
        r'''get the errors
either set_error('axisname',error_for_axis) or set_error(error_for_data)'''
        if (len(args) is 0):
            if self.data_error is None:
                return None
            else:
                return real(self.data_error)
        elif (len(args) is 1) and (type(args[0]) is str):
            if self.axis_coords_error[self.axn(args[0])] is None:
                return None
            else:
                x = self.axis_coords_error[self.axn(args[0])]
                if type(x) is ndarray:
                    if x.shape == ():
                        return None
                    else:
                        return real(self.axis_coords_error[self.axn(args[0])])
                else:
                    return real(self.axis_coords_error[self.axn(args[0])])
        else:
            raise CustomError('Not a valid argument to get_error')
    #}}}
    #{{{ add any dimensions to self that are not present in other
    def matchdims(self,other):
        #print 'diagnose: matching',ndshape(self),'to',ndshape(other)
        addeddims =  list(set(self.dimlabels)^set(other.dimlabels))
        newdims = addeddims + self.dimlabels
        newshape = [1]*len(addeddims) + list(self.data.shape)
        #print 'diagnose: newshape',newshape,'newdims',newdims
        #{{{ reshape to the new dimensions  
        new_axis_coords = [r_[1]]*len(addeddims) + self.axis_coords
        self.data = self.data.reshape(newshape)
        self.dimlabels = newdims
        if len(self.axis_coords)>0:
            self.axis_coords = new_axis_coords
        #}}}
        #{{{ if we are adding dimensions, we will need to reorder to match the order of the other   
        if len(addeddims)>0:
            self.reorder(other.dimlabels)
        #}}}
        return self
    #}}}
    def rename(self,previous,new):
        self.dimlabels[self.dimlabels.index(previous)] = new
        return self
    def set_prop(self,propname,val):
        self.other_info.update({propname:val})
        return
    def get_prop(self,propname):
        return self.other_info[propname]
    def set_plot_color(self,thiscolor):
        if thiscolor is None:
            return
        if thiscolor is str:
            colordict = {'r':[1,0,0],
                    'g':[0,1,0],
                    'b':[0,0,1],
                    'k':[0,0,0],
                    'y':[0.5,0.5,0],
                    'o':[0.75,0.25,0],
                    'c':[0,0.5,0.5]}
            try:
                thiscolor = colordict[thiscolor]
            except:
                raise CustomError('Color',thiscolor,'not in dictionary')
        self.other_info.update({'plot_color':thiscolor})
        return
    def get_plot_color(self):
        if 'plot_color' in self.other_info.keys():
            return self.other_info['plot_color']
        else:
            return None
    def __add__(self,arg):
        a = self.copy()
        if isscalar(arg):
            a.data += arg
            return a
        b = arg.copy()
        if (shape(arg.data)!=shape(a.data)):
            a.matchdims(b)
            b.matchdims(a)
        a.data += b.data
        Aerr = a.get_error()
        Berr = arg.get_error()
        if (Aerr is not None) or (Berr is not None):
            sigma = 0
            if Aerr != None:
                sigma += Aerr**2
            if Berr != None:
                sigma += Berr**2
            a.set_error(sqrt(sigma))
        return a
    def __sub__(self,arg):
        a = self.copy()
        if isscalar(arg):
            a.data -= arg
            return a
        b = arg.copy()
        if (shape(arg.data)!=shape(a.data)):
            a.matchdims(b)
            b.matchdims(a)
        a.data -= b.data
        Aerr = a.get_error()
        Berr = arg.get_error()
        if (Aerr is not None) or (Berr is not None):
            sigma = 0
            if Aerr != None:
                sigma += Aerr**2
            if Berr != None:
                sigma += Berr**2
            a.set_error(sqrt(sigma))
        return a
    def __mul__(self,arg):
        #{{{ do scalar multiplication
        if isscalar(arg):
            newdata = self.copy()
            newdata.data *= arg
            return newdata
        #}}}
        #{{{ collect the list of dimensions
        newdimlabels = list(self.dimlabels)
        temp = list(arg.dimlabels)
        for item in temp:
            if not (item in newdimlabels):
                newdimlabels += [item]
        #}}}
        #{{{collect the new orderings
        leftorder = []
        leftsize = ones(len(newdimlabels))
        j=0
        for item in newdimlabels:
            if item in self.dimlabels:
                thisindex = self.dimlabels.index(item)
                leftorder += [thisindex]
                leftsize[j] = self.data.shape[thisindex]
            j+=1
        #}}}
        rightorder = []
        rightsize = ones(len(newdimlabels))
        j=0
        for item in newdimlabels:
            if item in arg.dimlabels:
                thisindex = arg.dimlabels.index(item)
                rightorder += [thisindex]
                rightsize[j] = arg.data.shape[thisindex]
            j+=1
        result = self.data.copy().transpose(leftorder).reshape(leftsize) * arg.data.transpose(rightorder).reshape(rightsize)
        if len(self.axis_coords)>0:
            return nddata(result,list(result.shape),newdimlabels,axis_coords=list(self.axis_coords))
        else:
            return nddata(result,list(result.shape),newdimlabels)
    def aligndata(self,arg):
        r'''return the information needed to reshape both self and arg, such that any extra dimensions from arg are tacked on to those from self --> this allows multiplication + division where dimensions may not match in the numpy sense'''
        augmentdims = [x for x in arg.dimlabels if x in set(self.dimlabels)^set(arg.dimlabels)] # dims in arg but now self, ordered as they were in arg
        newdims = self.dimlabels + augmentdims # this should return the new dimensions with the order of self preserved, followed by augmentdims
        selfshape = list(self.data.shape)+list(ones(len(augmentdims))) # there is no need to transpose self, since its order is preserved
        new_arg_labels = [x for x in newdims if x in arg.dimlabels] # only the labels valid for B, ordered as they are in newdims
        argshape = list(ones(len(newdims)))
        #{{{ wherever the dimension exists in arg, pull the shape from arg
        for j,k in enumerate(newdims):
            if k in arg.dimlabels:
                argshape[j] = arg.data.shape[arg.dimlabels.index(k)]
        #}}}
        argorder = map(arg.dimlabels.index,new_arg_labels) # for each new dimension, determine the position of the original dimension
        return selfshape,argshape,newdims,argorder
    def __div__(self,arg):
        if isscalar(arg):
            A = self.copy()
            A.data /= arg
            if A.get_error() != None:
                error = A.get_error()
                error /= arg
            return A
        Ashape,Bshape,newdimlabels,Border= self.aligndata(arg)
        A = self.data.copy().reshape(Ashape)
        B = arg.data.copy().transpose(Border).reshape(Bshape)
        result = A / B
        #{{{ if we have error for both the sets of data, I should propagate that error
        Aerr = None
        Berr = None
        if self.get_error() != None:
            Aerr = self.get_error().copy().reshape(Ashape)
        if arg.get_error() != None:
            Berr = arg.get_error().copy().transpose(Border).reshape(Bshape)
        Rerr = 0.0 # we can have error on one or both, so we're going to need to add up the variances
        if Aerr != None:
            Rerr += (Aerr/B)**2
        if Berr != None:
            Rerr += (A*Berr/(B**2))**2
        Rerr = sqrt(real(Rerr)) # convert back to stdev
        #print "Rerr dtype",Rerr.dtype
        if Aerr == None and Berr == None:
            Rerr = None
        #}}}
        if len(self.axis_coords)>0:
            retval = nddata(result,list(result.shape),newdimlabels,axis_coords=list(self.axis_coords),data_error = Rerr)
            #{{{ handle the axis_coords_error directly, since it's a dictionary
            errordict = retval.mkd()
            #{{{ add the errors for B
            if type(arg.axis_coords_error) is list:
                if len(arg.axis_coords_error) > 0:
                    errordict.update(arg.mkd(arg.axis_coords_error))
            #}}}
            #{{{ add the errors for A
            if type(self.axis_coords_error) is list:
                if len(self.axis_coords_error) > 0:
                    errordict.update(self.mkd(self.axis_coords_error))
            #}}}
            #}}}
            retval.axis_coords_error = retval.fld(errordict)
            return retval
        else:
            return nddata(result,list(result.shape),newdimlabels,data_error = Rerr)
    def integrate(self,thisaxis,backwards = False):
        if backwards is True:
            self.data = self[thisaxis,::-1].data
        self.run_nopop(cumsum,thisaxis)
        if backwards is True:
            self.data = self[thisaxis,::-1].data
        if len(self.axis_coords)>0:
            t = self.getaxis(thisaxis)
            dt = t[1]-t[0]
            self.data *= dt
        return self
    def polyfit(self,axis,order=1,force_y_intercept = None):
        'return the coefficients and the fit --> later, should probably branch this off as a new type of fit class'
        x = self.getaxis(axis).copy().reshape(-1,1)
        #{{{ make a copy of self with the relevant dimension second to last (i.e. rows)
        formult = self.copy()
        neworder = list(formult.dimlabels)
        neworder.pop(neworder.index(axis))
        if len(neworder) > 1:
            neworder = neworder[:-1] + [axis] + neworder[-1]
        else:
            neworder = [axis] + neworder
        formult.reorder(neworder)
        #}}}
        y = formult.data
        #{{{ now solve Lx = y, where x is appropriate for our polynomial
        startingpower = 0
        if force_y_intercept != None:
            startingpower = 1
        L =  concatenate([x**j for j in range(startingpower,order+1)],axis=1) # note the totally AWESOME way in which this is done!
        #print 'fitting to matrix',L
        if force_y_intercept != None:
            y -= force_y_intercept
        c = dot(pinv(L),y)
        fity = dot(L,c)
        if force_y_intercept != None:
            #print "\n\nDEBUG: forcing from",fity[0],"to"
            fity += force_y_intercept
            #print "DEBUG: ",fity[0]
            c = c_[force_y_intercept,c]
        #}}}
        #{{{ rather than have to match up everything, just drop the fit data into formult, which should be the same size, shape, etc
        formult.data = fity
        #}}}
        return c,formult
    def sum(self,axes):
        if (type(axes) is str):
            axes = [axes]
        for j in range(0,len(axes)):
            try:
                thisindex = self.dimlabels.index(axes[j])
            except:
                print '|-ERROR FINDING DIMENSION-----'
                print '| dimlabels is: ',self.dimlabels
                print "| doesn't contain: ",axes[j]
                print '|-----------------------------'
                raise
            self.data = sum(self.data,
                    axis=thisindex)
            self.dimlabels.pop(thisindex)
            if self.axis_coords!=[]:
                self.axis_coords.pop(thisindex)
        return self
    def argmax(self,axes):
        if (type(axes) is str):
            axes = [axes]
        for j in range(0,len(axes)):
            try:
                thisindex = self.dimlabels.index(axes[j])
            except:
                print 'error, dimlabels is: ',self.dimlabels
                print "doesn't contain: ",axes[j]
                raise
            self.data = argmax(self.data,
                    axis=thisindex)
            self.dimlabels.pop(thisindex)
            if self.axis_coords!=[]:
                self.axis_coords.pop(thisindex)
        return self
    def mean_all_but(self,listofdims):
        'take the mean over all dimensions not in the list'
        for dimname in self.dimlabels:
            if not (dimname in listofdims):
                self.mean(dimname)
        return self
    def mean(self,axes):
        if (type(axes) is str):
            axes = [axes]
        for j in range(0,len(axes)):
            try:
                thisindex = self.dimlabels.index(axes[j])
            except:
                print 'error, dimlabels is: ',self.dimlabels
                print "doesn't contain: ",axes[j]
                raise
            self.data = mean(self.data,
                    axis=thisindex)
            self.dimlabels.pop(thisindex)
            if self.axis_coords!=[]:
                self.axis_coords.pop(thisindex)
        return self
    def mean_nopop(self,axis):
        self = self.run_nopop(mean,axis=axis)
        return self
    def sum_nopop(self,axes):
        if (type(axes) is str):
            axes = [axes]
        for j in range(0,len(axes)):
            try:
                thisindex = self.dimlabels.index(axes[j])
            except:
                print 'error, dimlabels is: ',self.dimlabels
                print "doesn't contain: ",axes[j]
                raise
            temp = list(self.data.shape)
            temp[thisindex] = 1
            self.data = sum(self.data,
                    axis=thisindex)
            self.data = self.data.reshape(temp)
        return self
    def popdim(self,dimname):
        thisaxis = self.axn(dimname)
        thisshape = list(self.data.shape)
        if thisshape[thisaxis]!=1:
            raise CustomError("trying to pop a dim that's not length 1")
        thisshape.pop(thisaxis)
        self.data = self.data.reshape(thisshape)
        self.dimlabels.pop(thisaxis)
        self.axis_coords.pop(thisaxis)
        try:
            self.axis_coords_error.pop(thisaxis)
        except:
            raise CustomError('trying to pop',thisaxis,'from',self.axis_coords_error)
        #self.axis_coords_units.pop(thisaxis)
        return self
    def convolve(self,axisname,filterwidth,convfunc = (lambda x,y: exp(-(x**2)/(2.0*(y**2))))):
        r'''perform a normalized convolution'''
        #{{{ make a version of x that is oriented along the correct dimension
        thisaxis = self.dimlabels.index(axisname)
        newshape = [1] * len(self.data.shape)
        x = self.getaxis(axisname).copy().flatten()
        x = x-x.mean()
        newshape[thisaxis] = len(x)
        x.reshape(newshape)
        #}}}
        myfilter = convfunc(x,filterwidth)
        myfilter /= myfilter.sum()
        self.data = fftconvolve(self.data,myfilter,mode='same') # I need this, so the noise doesn't break up my blocks
        return self
    def multimin(self,minfunc,axisname,filterwidth,numberofmins):
        cost = self.copy().convolve(axisname,filterwidth).run_nopop(minfunc)
        for j in range(0,numberofmins):
            #{{{ find the x value at which the minimum occurs
            xvalues = cost.copy().argmin(axisname)
            #}}}
    def repwlabels(self,axis):
        return None
    def argmin(self,axis):
        thisaxis = self.dimlabels.index(axisname)
        self.data = argmin(thisaxis,axis = thisaxis)
        x = self.getaxis(axis)
        newdata = x[self.data]
        self.data = newdata
        return self
    def ft(self,axes,shiftornot=False,shift=None):
        if shift != None:
            shiftornot = shift
        if (type(axes) is str):
            axes = [axes]
        if not (type(shiftornot) is list):
            shiftornot = [bool(shiftornot)]
        for j in range(0,len(axes)):
            try:
                thisaxis = self.dimlabels.index(axes[j])
            except:
                raise CustomError('error, dimlabels is: ',self.dimlabels)
            self.data = fft(self.data,axis=thisaxis)
            if bool(shiftornot[j]):
                self.data = fftshift(self.data,axes=[thisaxis])
            if len(self.axis_coords)>0:
                t = self.axis_coords[thisaxis]
                dt = t[1]-t[0]
                self.ft_start_time = t[0]
                self.data *= dt
                self.axis_coords[thisaxis] = linspace(0,1./dt,size(t))
                if bool(shiftornot[j]):
                    mask = self.axis_coords[thisaxis] > 0.5/dt
                    self.axis_coords[thisaxis][mask] -= (1.+1./size(t))/dt
                    self.axis_coords[thisaxis] = fftshift(self.axis_coords[thisaxis])
        return self
    def ift(self,axes,shiftornot=False,shift=None):
        if shift != None:
            shiftornot = shift
        if (type(axes) is str):
            axes = [axes]
        if not (type(shiftornot) is list):
            shiftornot = [bool(shiftornot)]
        for j in range(0,len(axes)):
            try:
                thisaxis = self.dimlabels.index(axes[j])
            except:
                raise CustomError('error, dimlabels is: ',self.dimlabels)
            if bool(shiftornot[j]):
                self.data = ifftshift(self.data,axes=[thisaxis])
            self.data = ifft(self.data,axis=thisaxis)
            if len(self.axis_coords)>0:
                t = self.axis_coords[thisaxis]
                dt = t[1]-t[0]
                self.data *= size(t) * dt # here, the algorithm divides by N, so for integration, we need to not do that
                #{{{ shiftornot specifies the shifting of the initial ft, not this result, so we always return a 0->1 time axis
                self.axis_coords[thisaxis] = linspace(0,1./dt,size(t)) + self.ft_start_time # note that I offset by ft_start_time, which I pull from when I ft'd
                #}}}
        return self
    def __abs__(self):
        return self.runcopy(abs)
    def runcopy(self,*args):
        newdata = self.copy()
        func = args[0]
        func = self._wrapaxisfuncs(func)
        if len(args)>1:
            axis = args[1]
            thisaxis = newdata.dimlabels.index(axis)
            newdata.data = func(newdata.data,axis=thisaxis)
            newdata.dimlabels.pop(thisaxis)
            if newdata.axis_coords!=[]:
                newdata.axis_coords.pop(thisaxis)
        else:
            newdata.data = func(newdata.data)
        return newdata
    def circshift(self,axis,amount):
        if amount!=0:
            if abs(amount) > ndshape(self)[axis]:
                CustomError("Trying to circshift by ",amount,"which is bitter than the size of",axis)
            newdata = ndshape(self).alloc(dtype=self.data.dtype)
            newdata[axis,:-amount] = self[axis,amount:]
            newdata[axis,-amount:] = self[axis,:amount]
            self.data = newdata.data
        return self
    def labels(self,listofstrings,listofaxes):
        if len(self.axis_coords) == 0:
            self.axis_coords = [[]]*len(self.dimlabels)
            self.axis_coords_error = [None]*len(self.dimlabels)
        for j in range(0,len(listofstrings)):
            #{{{ test that the axis is the right size
            if type(listofstrings) is not list:
                raise CustomError("the arguments passed to the .labels() method must be a list of the axis names followed by the list of the axis arrays")
            if (len(listofaxes[j]) != ndshape(self)[listofstrings[j]]) and (len(listofaxes[j])!=0):
                raise CustomError("You're trying to attach an axis of len",len(listofaxes[j]),"to the",listofstrings[j],"dimension, which has ",ndshape(self)[listofstrings[j]]," data points")
            #}}}
            try:
                self.axis_coords[self.dimlabels.index(listofstrings[j])] = listofaxes[j]
            except:
                try:
                    raise CustomError("Can't assign the coordinates to"+listofstrings[j]+"as"+listofaxes[j].__repr__())
                except:
                    raise CustomError("listofaxes (",len(listofaxes),") isn't same length as ",listofstrings)
        return self
    def sort(self,axisname):
        whichaxis = self.dimlabels.index(axisname)
        order = argsort(self.axis_coords[whichaxis])
        datacopy = self.copy()
        for j in range(0,len(order)): # do it this way, so that it deals with other dimensions correctly
            self[axisname,j] = datacopy[axisname,order[j]]
        self.axis_coords[whichaxis] = self.axis_coords[whichaxis][order]
        return self
    def copyaxes(self,other):
        # in the case that the dimensions match, and we want to copy the labels
        self.axis_coords = other.axis_coords
        return self
    def retaxis(self,axisname):
        return nddata(self.getaxis(axisname).copy(),[size(self.getaxis(axisname))],[axisname])
    def getaxis(self,axisname):
            return self.axis_coords[self.dimlabels.index(axisname)]
    def getaxisshape(self,axisname):
        thishape = ones(len(self.dimlabels))
        thisaxis = self.dimlabels.index(axisname) 
        thishape[thisaxis] = self.data.shape[thisaxis]
        return thishape
    def run(self,*args):
        func = args[0]
        func = self._wrapaxisfuncs(func)
        if len(args)>1:
            axis = args[1]
            thisaxis = self.dimlabels.index(axis)
            self.data = func(self.data,axis=thisaxis)
            self.dimlabels.pop(thisaxis)
            if self.axis_coords!=[]:
                self.axis_coords.pop(thisaxis)
        else:
            self.data = func(self.data)
        return self
    def _wrapaxisfuncs(self,func):
        #{{{ for convenience, wrap the max and min functions
        if func == max:
            func = amax
        if func == min:
            func = amin
        if func == diff:
            func = mydiff
        return func
        #}}}
    def run_nopop(self,func,axis):
        func = self._wrapaxisfuncs(func)
        try:
            thisaxis = self.dimlabels.index(axis)
        except:
            raise CustomError("I couldn't find the dimension",axis,"in the list of axes",self.dimlabels)
        temp = list(self.data.shape)
        temp[thisaxis] = 1
        numnonoptargs = len(getargspec(func)[0])-len(getargspec(func)[3])
        if numnonoptargs == 1:
            self.data = func(self.data,axis=thisaxis)
        elif numnonoptargs == 2:
            self.data = func(self.getaxis(axis),self.data,axis=thisaxis)
        else:
            raise CustomError('you passed a function to run_nopop that doesn\'t have either one or two arguments!')
        #{{{ if the function doesn't rip out the dim, make sure we don't change the dims
        if len(self.data.shape)==len(temp):
            temp[thisaxis] = self.data.shape[thisaxis]
        #}}}
        self.data = self.data.reshape(temp)
        return self
    def smash(self,listofhowmany):
        r'''collapse multiple dimensions into one dimension'''
        names = ['error'] * len(listofhowmany)
        newsize = []
        laststop = 0 
        j = 0
        for ndims in listofhowmany:
            thisstop = laststop + ndims
            newsize += [prod(self.data.shape[laststop:thisstop])]
            names[j] = ' x '.join(self.dimlabels[laststop:thisstop])
            laststop = thisstop
            j+=1
        self.data = self.data.reshape(newsize)
        self.dimlabels = names
        return self
    def smashorder(self,listoflists):
        self.reorder(concatenate(listoflists))
        self.smash(map(len,listoflists))
        return self
    def chunk(self,axisin,axesout,shapesout):
        if prod(shapesout) != ndshape(self)[axisin]:
            raise CustomError("The size of the axis you're trying to split doesn't match the size of the axes you're trying to split it into")
        thisaxis = self.dimlabels.index(axisin)
        if len(self.axis_coords[thisaxis]) > 0:
            raise CustomError("split not yet supported on axes with labels")
        newaxis_coords = self.axis_coords[0:thisaxis] + [[]]*len(axesout) + self.axis_coords[thisaxis+1:]
        newaxis_coords_error = self.axis_coords_error[0:thisaxis] + [None]*len(axesout) + self.axis_coords_error[thisaxis+1:]
        newshape = list(self.data.shape[0:thisaxis]) + shapesout + list(self.data.shape[thisaxis+1:])
        newnames = list(self.dimlabels[0:thisaxis]) + axesout + list(self.dimlabels[thisaxis+1:])
        self.data = self.data.reshape(newshape)
        self.dimlabels = newnames
        self.axis_coords = newaxis_coords
        self.axis_coords_error = newaxis_coords_error
        return self
    def chunkoff(self,axisin,newaxes,newshapes):
        r'''chunks up axisin, dividing it into newaxes with newshapes on the inside'''
        axesout = [axisin]+newaxes
        shapesout = [ndshape(self)[axisin]/prod(newshapes)]+newshapes
        return self.chunk(axisin,axesout,shapesout)
    def reorder(self,*axes):
        if len(axes) == 1:
            axes = axes[0]
        else:
            axes = axes
        try:
            neworder = map(self.dimlabels.index,axes)
        except ValueError:
            raise CustomError('one of',axes,'not in',self.dimlabels)
        self.dimlabels = map(self.dimlabels.__getitem__,neworder)
        if len(self.axis_coords)>0:
            try:
                self.axis_coords = map(self.axis_coords.__getitem__,neworder)
            except:
                raise CustomError('problem mapping',map(len,self.axis_coords),'onto',neworder)
        try:
            self.data = self.data.transpose(neworder)
        except ValueError:
            raise CustomError('you can\'t reorder',self.dimlabels,'as',neworder)
        return self
    def __getslice__(self,*args):
        print 'getslice! ',args
#    def __getattribute__(self,name):
#        if name == 'test':
#            return 0.
#        else:
#            return object.__getattribute__(self,name)
    def __setitem__(self,*args):
        if isinstance(args[1],nddata):
            rightdata = args[1].data
            #print 'check size:',self.data.shape,args[1].data.shape
            rightlabels = args[1].dimlabels
        else: # assume it's an ndarray
            rightdata = args[1]
            if (type(rightdata) is not ndarray): # in case its a scalar
                rightdata = array([rightdata])
        #{{{ build up the left index list
        leftindex = [slice(None,None,None)]*len(self.dimlabels) # by default, just pass everything, to cut the :,:,: notation
        for j in range(0,len(args[0]),2):
            try:
                thisindex = self.dimlabels.index(args[0][j]) # find the number of the dimension we're about to index
            except:
                print 'ERROR------------------------'
                print args[0][j],' not found'
                print '-----------------------------'
                raise
            leftindex[thisindex] = args[0][j+1] # substitute the default value of the index with the new value
        #}}}
        try:
            self.data[tuple(leftindex)] = rightdata.squeeze() # assign the data
        except:
            raise CustomError('ERROR ASSIGNING NDDATA:','rightdata.shape:',rightdata.shape,'self.data.shape:',self.data.shape,' dimlabels:',self.dimlabels,' leftindex:',tuple(leftindex),'--> shape of left slice: ',self.data[tuple(leftindex)].shape)
            raise
        #print 'STOP SETITEM --------------------------------'
    def copy(self):
        return deepcopy(self)
    def __getitem__(self,args):
        #print "DEBUG getitem called with",args
        if type(args[0]) is str:
            slicedict = dict(zip(list(self.dimlabels),[slice(None,None,None)]*len(self.dimlabels))) #initialize to all none
            if len(self.axis_coords)>0:
                axesdict = self.mkd(self.axis_coords)
                errordict = self.mkd(self.axis_coords_error)
                #print 'DEBUG: made errordict',errordict
            #{{{ store the passed slices appropriately
            for x,y in zip(args[0::2],args[1::2]):
                slicedict[x] = y
            #}}}
            #{{{ map the slices onto the axis coordinates and errors
            #print "DEBUG slicedict is",slicedict
            if len(self.axis_coords)>0:
                for x,y in slicedict.iteritems():
                    #print "DEBUG, type of slice",x,"is",type(y)
                    if isscalar(y):
                        axesdict.pop(x) # pop the axes for all scalar dimensions
                    elif type(y) is type(emptyfunction):
                        mask = y(axesdict[x])
                        slicedict[x] = mask
                        axesdict[x] = axesdict[x][mask]
                    else:
                        axesdict[x] = axesdict[x][y]
                if errordict != None and errordict != array(None):
                    for x,y in slicedict.iteritems():
                        if errordict[x] != None:
                            if isscalar(y):
                                errordict.pop(x)
                            elif type(y) is type(emptyfunction):
                                mask = y(axesdict[x])
                                errordict[x] = errordict[x][mask]
                            else:
                                try:
                                    errordict[x] = errordict[x][y] # default
                                except:
                                    raise CustomError('Trying to index',errordict,'-->',x,'=',errordict[x],'with',y,'error started as',self.axis_coords_error)
                    errordict = self.mkd().update(errordict) # make everything none except the ones I've updated
            #}}}
            indexlist = [slicedict[x] for x in self.dimlabels]# generate the new list of slices, in the correct order, by mapping getitem onto self.dimlabels
            newlabels = [x for x in self.dimlabels if not isscalar(slicedict[x])] # generate the new list of labels, in order, for all dimensions that are not indexed by a scalar
            #{{{ properly index the data error
            if self.data_error != None:
                newerror = self.data_error[indexlist]
            else:
                newerror = None
            #}}}
            if len(self.axis_coords)>0:
                if errordict != None:
                    axis_coords_error = [errordict[x] for x in newlabels]
                else:
                    axis_coords_error = None
                return nddata(self.data[indexlist],
                        self.data[indexlist].shape,
                        newlabels,
                        axis_coords = [axesdict[x] for x in newlabels],
                        axis_coords_error = axis_coords_error,
                        data_error = newerror)
            else:
                return nddata(self.data[indexlist],self.data[indexlist].shape,newlabels)
        else:
            print 'label your freaking dimensions!'
            #print 'STOP GETITEM --------------------------------'
            raise
#}}}

#{{{subplot_dim
class subplot_dim():
    def __init__(self,firstdim,seconddim):
        self.num = r_[firstdim,seconddim,0]
    def set(self,args,x='',g=True,y='',t='',a=''):
        if type(args) is int:
            number = args
            ax = subplot(*tuple(self.num+r_[0,0,number]))
            xlabel(x)
            ylabel(y)
            title(t)
            grid(g)
        elif (type(args) is tuple) and (len(args) is 3):
            # the second value passed is 
            whichsmall = args[2]
            break_into = args[1]
            number = args[0]
            mydims = self.num*r_[1,break_into,1]+r_[
                    0,0,break_into*(number-1)+whichsmall]
            try:
                ax = subplot(*tuple(mydims))
            except:
                print 'failed trying subplots: ', mydims
                raise
            xlabel(x)
            ylabel(y)
            title(t)
            grid(g)
        else:
            print "problem, need to pass either 1 or 3 arguments to set"
            print 'type of args: ',type(args)
        return ax
#}}}
def fa(input,dtype='complex128'):# make a fortran array
    return array(input,order='F',dtype=dtype) # will need transpose reverses the dimensions, since the bracketing still works in C order (inner is last index), but F tells it to store it appropriately in memory
def ndgrid(*input):
    thissize = list([1])
    thissize = thissize * len(input)
    output = list()
    for j in range(0,len(input)):
        tempsize = copy(thissize)
        tempsize[j] = input[j].size
        output.append(input[j].reshape(tempsize))
    return output
def pinvr(C,alpha):
    print 'pinvr called'
    U,S,V = svd(C,full_matrices=0)
    #print 'U S V shapes:'
    #print U.shape
    #print S.shape
    #print V.shape
    if any(~isfinite(U)):
        raise CustomError('pinvr error, U is not finite')
    if any(~isfinite(V)):
        raise CustomError('pinvr error, V is not finite')
    if any(~isfinite(S)):
        raise CustomError('pinvr error, S is not finite')
    S = diag(S / (S**2 + alpha**2))
    if any(~isfinite(S)):
        raise CustomError('pinvr error, problem with S/(S^2+alpha^2) --> set your regularization higher')
    return dot(conj(transpose(V)),
            dot(S,conj(transpose(U))))
def sech(x):
    return 1./cosh(x)
def spectrogram(waveform,f_start,f_stop,npoints_fdom=40,tdom_div=2):
    #npoints_tdom = int(round(double(waveform.len)/double(npoints_fdom)))*npoints_tdom_mult
    npoints_tdom = waveform.len/tdom_div # this seems to be more legible than above 
    resolution = diff(waveform.x[0:2])

    sigma = abs(f_start-f_stop)/double(npoints_fdom)
    #print "sigma = %f resolution = %f"%(sigma,resolution)
    if sigma<4*resolution:
        sigma = 4*resolution

    waveform.def_filter(sigma,npoints_tdom)# define the filter and number of points for the spectrogram windowing (define the filter such that the points are spaced sigma apart)

    # go through and apply the filter for some range of points

    f_axis = linspace(f_start,f_stop,npoints_fdom)

    specgram = zeros((npoints_fdom,npoints_tdom),dtype="complex128")

    for j in range(0,npoints_fdom):

        t_axis, specgram[j,:] = waveform.do_filter(f_axis[j])
        #plot(t_axis,abs(specgram[j,:])) # leave this in for testing what it does in the fdom
    #image(specgram,y=f_axis/1e6,x=t_axis*1e6) # now do an imagehsv (see if we can make imagerybw) plot of the resulting spectrogram
    imshow(abs(specgram),extent=(t_axis[0]*1e6,t_axis[-1]*1e6,f_axis[-1]/1e6,f_axis[0]/1e6)) # now do an imagehsv (see if we can make imagerybw) plot of the resulting spectrogram
    return gca()
def image(A,x=[],y=[],**kwargs):
    setlabels = False
    if isinstance(A,nddata):
        setlabels = True
        templabels = list(A.dimlabels)
        x_label = templabels[-1]
        x = list(A.getaxis(x_label))
        templabels.pop(-1)
        y_label = ''
        while len(templabels)>0:
            y_label += templabels.pop(0)
            if len(templabels)>0:
                y_label += r' $\times$ '
        A = A.data
    if type(x) is list:
        x = array(x)
    if type(y) is list:
        y = array(y)
    if len(x)==0:
        x = [1,A.shape[1]]
    else:
        x = x.flatten()
    if len(y)==0:
        y = [1,A.shape[0]]
    else:
        y = y.flatten()
    myext = (x[0],x[-1],y[-1],y[0])
    extralines = 0
    while A.ndim>2:# to substitude for imagehsvm, etc., so that we just need a ersion of ft
        # order according to how it's ordered in the memory
        # the innermost two will form the image -- first add a line to the end of the images we're going to join up
        tempsize = array(A.shape) # make a tuple the right shape
        tempsize[-2] = 1 # all dims are the same except the image row, of which there is only one
        A = concatenate((A,nan*zeros(tempsize)),axis=(A.ndim-2)) # concatenate along the rows
        tempsize = r_[A.shape[0:-3],A.shape[-2:]]
        tempsize[-2] *= A.shape[-3]
        A = A.reshape(tempsize) # now join them up
        ++extralines # keep track of the extra lines at the end
    A = A[:A.shape[0]-extralines,:]
    line_mask = isnan(A)
    #A[line_mask] = A[logical_not(line_mask)].max()
    A[line_mask] = 0
    if iscomplex(A).any():
        A = imagehsv(A)
        imshow(A,extent=myext,**kwargs)
    else:
        imshow(A,extent=myext,**kwargs)
        colorbar()
    if setlabels:
        xlabel(x_label)
        #print y_label
        ylabel(y_label)
    return
def colormap(points,colors,n=256):
    r = interp(linspace(0,1,n),points,colors[:,0].flatten())
    g = interp(linspace(0,1,n),points,colors[:,1].flatten())
    b = interp(linspace(0,1,n),points,colors[:,2].flatten())
    return reshape(r_[r,g,b],(3,n)).T
def imagehsv(A):
    n = 256
    theta = (n-1.)*mod(angle(A)/pi/2.0,1)# angle in 255*cycles
    hsv = colormap(r_[0.,1./3.,2./3.,1.],double(array([
        [1,0,0],
        [0,1,0],
        [0,0,1],
        [1,0,0]])),n=n)
    hsv_norm = sqrt(sum(hsv*hsv,axis=1))
    hsv_norm = reshape(hsv_norm,(hsv_norm.size,1))
    hsv = hsv/hsv_norm
    colors = hsv[ix_(int32(theta.flatten().round()),[0,1,2])]
    colors = reshape(colors,(A.shape[0],A.shape[1],3))
    colors *= abs(A).reshape(A.shape[0],A.shape[1],1)
    colors /= abs(A).max()
    return colors
def myfilter(x,center = 250e3,sigma = 100e3):
    x = (x-center)**2
    x /= sigma**2
    return exp(-x)
#}}}

#{{{ fitdata
class fitdata(nddata):
    def __init__(self,*args,**kwargs):
        if 'fit_axis' in kwargs.keys():
            fit_axis = kwargs.pop('fit_axis')
        else:
            fit_axis = 't2'
        if isinstance(args[0],nddata):
            #print "DEBUG trying to transfer",args[0].axis_coords_error
            nddata.__init__(self,
                    args[0].data,
                    args[0].data.shape,
                    args[0].dimlabels,
                    axis_coords = args[0].axis_coords,
                    ft_start_time = args[0].ft_start_time,
                    data_error = args[0].data_error,
                    axis_coords_error = args[0].axis_coords_error,
                    axis_coords_units = args[0].axis_coords_units,
                    data_units = args[0].data_units,
                    other_info = args[0].other_info,
                    **kwargs)
            self.fit_axis = fit_axis
        else:
            #self.__base_init(*args,**kwargs)
            nddata.__init__(self,*args,**kwargs)
            self.fit_axis = fit_axis
        #{{{ in the class, only store the forced values and indeces they are set to
        self.set_to = None
        self.set_indeces = None
        self.active_indeces = None
        #}}}
        return
    def copy(self): # for some reason, if I don't override this with the same thing, it doesn't override
        return deepcopy(self)
    def gen_indeces(self,set,set_to):
        r'''pass this set and set\_to parameters, and it will return:
        indeces,values,mask
        indeces --> gives the indeces that are forced
        values --> the values they are forced to
        mask --> p[mask] are actually active in the fit'''
        if type(set) is not list:
            set = [set]
        if type(set_to) is not list:
            set_to = [set_to]
        set_indeces = map(self.symbol_list.index,set) # calculate indeces once for efficiency
        active_mask = ones(len(self.symbol_list),dtype = bool)
        active_mask[set_indeces] = False # generate the mask of indeces that are actively fit
        return set_indeces,set_to,active_mask
    def fitfunc(self,p,x):
        r"this wraps fitfunc_raw (which gives the actual form of the fit function) to take care of forced variables"
        if self.set_indeces != None:
            #{{{ uncollapse the function
            temp = p.copy()
            p = zeros(len(self.symbol_list))
            p[self.active_mask] = temp
            #}}}
            p[self.set_indeces] = self.set_to # then just set the forced values to their given values
            #print "DEBUG trying to uncollapse in fitfunc w/ ",self.symbol_list,"; from",temp,"to",p
        return self.fitfunc_raw(p,x)
    def errfunc(self,p,x,y,sigma):
        '''just the error function'''
        fit = self.fitfunc(p,x)
        try:
            retval = (y-fit)/sigma
        except ValueError:
            raise CustomError('your error (',shape(sigma),') probably doesn\'t match y (',shape(y),') and fit (',shape(fit),')')
        return retval
    def pinv(self,*args,**kwargs):
        if 'verbose' in kwargs.keys():
            verbose = kwargs.pop('verbose')
        else:
            verbose = False
        retval = self.linear(*args,**kwargs)
        y = retval.data
        yerr = retval.get_error()
        x_axis = retval.dimlabels[0]
        x = retval.getaxis(x_axis)
        nopowerindex = argmax(x)
        mask = logical_not(r_[0:len(x)] == nopowerindex)
        y = y[mask]
        yerr = yerr[mask]
        x = x[mask]
        L = c_[x.reshape((-1,1)),ones((len(x),1))]
        retval = dot(pinv(L,rcond = 1e-17),y)
        if verbose:
            print r'\label{fig:pinv_figure_text}y=',y,'yerr=',yerr,'%s='%x_axis,x,'L=',L
            print '\n\n'
            print 'recalc y = ',dot(L,retval)
            print 'recalc E = ',1.0-1.0/dot(L,retval)
            print 'actual E = ',self.data
        return retval
    def linear(self,*args,**kwargs):
        r'''return the linear-form function, either smoothly along the fit function, or on the raw data, depending on whether or not the taxis argument is given
        can take optional arguments and pass them on to eval'''
        #print "DEBUG called linear"
        if len(args) > 0:
            retval = self.linfunc(args[0],self.eval(args[0],**kwargs).data) # if we pass an argument, return the function across the entire time axis passed
        else:
            retval = self.linfunc(self.getaxis(self.fit_axis),self.data,yerr = self.get_error(),xerr = self.get_error(self.fit_axis)) # otherwise, return the raw data
        return retval
    def output(self,*name):
        r'''give the fit value of a particular symbol'''
        p = self.fit_coeff.copy()
        if self.set_indeces != None:
            #{{{ uncollapse the function
            temp = p.copy()
            p = zeros(len(self.symbol_list))
            p[self.active_mask] = temp
            #}}}
            p[self.set_indeces] = self.set_to # then just set the forced values to their given values
            #print "DEBUG trying to uncollapse in fitfunc w/ ",self.symbol_list,"; from",temp,"to",p
        # this should also be generic
        if len(name) is 1:
            try:
                return p[self.symbol_list.index(name[0])]
            except:
                raise CustomError("While running output: couldn't find",name,"in",self.symbol_list)
        elif len(name) is 0:
            # return a record array
            return array(tuple(p),{"names":list(self.symbol_list),"formats":['double']*len(p)}).reshape(1)
        else:
            raise CustomError("You can't pass",len(name),"arguments to .output()")
    def _pn(self,name):
        return self.symbol_list.index(name)
    def covar(self,*names):
        r'''give the covariance for the different symbols'''
        if len(names) == 1:
            names = [names[0],names[0]]
        return self.covariance[self._pn(names[0]),
                self._pn(names[1])].copy()
    def covarmat(self,*names):
        indeces = map(self._pn,names)
        return self.covariance[c_[indeces],r_[indeces]].copy()
    def latex(self):
        r'''show the latex string for the function, with all the symbols substituted by their values'''
        # this should actually be generic to fitdata
        p = self.fit_coeff
        printfstring = self.function_string
        printfargs = []
        allsymb = []
        locations = []
        for j in range(0,len(self.symbol_list)):
            symbol = self.symbol_list[j]
            location = printfstring.find(symbol)
            while location != -1:
                if printfstring[location-1] == '-':
                    newstring = printfstring[:location-1]+'+%01.03g'+printfstring[location+len(symbol):] # replace the symbol in the written function with the appropriate number
                    thissign = -1.0
                else:
                    newstring = printfstring[:location]+'%01.03g'+printfstring[location+len(symbol):] # replace the symbol in the written function with the appropriate number
                    thissign = 1.0
                #print r"\begin{verbatim} trying to replace",printfstring[location:location+len(symbol)],r'\end{verbatim}'
                printfstring = newstring
                printfargs += [thissign*p[j]] # add that number to the printf list
                locations += [location]
                allsymb += [symbol]
                location = printfstring.find(symbol)
        printfargs = [printfargs[x] for x in argsort(locations)]
        #print r"\begin{verbatim}trying to generate",self.function_string,'\n',printfstring,'\n',[allsymb[x] for x in argsort(locations)],'\n',printfargs,r'\end{verbatim}'
        return printfstring%tuple(printfargs)
    def eval(self,taxis,set = None,set_to = None):
        r'''after we have fit, evaluate the fit function along the axis taxis
        set and set_to allow you to forcibly set a specific symbol to a specific value --> however, this does not affect the class, but only the return value'''
        if type(taxis) is int:
            taxis = linspace( self.getaxis(self.fit_axis).min(),
                    self.getaxis(self.fit_axis).max(),
                    taxis)
        p = self.fit_coeff.copy()
        #{{{ LOCALLY apply any forced values
        if set != None:
            if self.set_indeces != None:
                raise CustomError("your'e trying to set indeces in an eval function for a function that was fit constrained; this is not currently supported")
            set_indeces,set_to,active_mask = self.gen_indeces(set,set_to)
            p[set_indeces] = set_to
        #}}}
        #{{{ make a new, blank array with the fit axis expanded to fit taxis
        newdata = ndshape(self)
        newdata[self.fit_axis] = size(taxis)
        newdata = newdata.alloc()
        newdata.set_plot_color(self.get_plot_color())
        #}}}
        #{{{ keep all axis labels the same, except the expanded one
        newdata.axis_coords = list(newdata.axis_coords)
        newdata.labels([self.fit_axis],list([taxis]))
        #}}}
        newdata.data[:] = self.fitfunc(p,taxis).flatten()
        return newdata
    def makereal(self):
        self.data = real(self.data)
        return
    def rename(self,previous,new):
        if previous == self.fit_axis:
            self.fit_axis = new
        nddata.rename(self,previous,new)
        return self
    def fit(self,set = None, set_to = None):
        r'''actually run the fit'''
        x = self.getaxis(self.fit_axis)
        y = self.data
        sigma = self.get_error()
        if sigma is None:
            sigma = ones(shape(y))
        p_ini = array(self.guess()) # need the numpy format to allow boolean mask
        if set != None:
            #print "DEBUG in fit, setting",set,"to",set_to
            self.set_indeces,self.set_to,self.active_mask = self.gen_indeces(set,set_to)
        if self.set_indeces != None:
            #print "DEBUG in collapsed",p_ini
            p_ini = p_ini[self.active_mask] # collapse p_ini
            #print "DEBUG to",p_ini
        try:
            p_out,cov,infodict,mesg,success = leastsq(self.errfunc, p_ini,
                    args = (x,y,sigma),
                    full_output = True)
        except:
            if type(x) != ndarray and type(y) != ndarray:
                raise CustomError('leastsq failed because the two arrays aren\'t of the right type','type(x):',type(x),'type(y):',type(y))
            else:
                if any(shape(x) != shape(y)):
                    raise CustomError('leastsq failed because the two arrays do not match in size size','shape(x):',shape(x),'shape(y):',shape(y))
                else:
                    raise CustomError('leastsq failed; I don\'t know why')
        if success != 1:
            if mesg.find('maxfev'):
                maxfev = 10000
                p_out,cov,infodict,mesg,success = leastsq(self.errfunc, p_ini,
                        args = (x,y,sigma),
                        maxfev = maxfev,
                        full_output = True)
                if success != 1:
                    if mesg.find('two consecutive iterates'):
                        print 'DBG:2 cons iter err'
                    else:
                        raise CustomError('leastsq finished with an error message:',mesg)
        self.covariance = cov
        # here, I do NOT uncollapse p_out, since fitfunc is wrapped to do so already
        self.fit_coeff = p_out
        return
    def bootstrap(self,points,swap_out = exp(-1.0),seedval = 10347,minbounds = {},maxbounds = {}):
        print r'\begin{verbatim}'
        seed(seedval)
        fitparameters = list(self.symbol_list)
        recordlist = array([tuple([0]*len(fitparameters))]*points,
                {'names':tuple(fitparameters),'formats':tuple(['double']*len(fitparameters))}) # make an instance of the recordlist
        for runno in range(0,points):
            success = False # because sometimes this doesn't work
            while success is False:
                thiscopy = self.copy()
                #{{{ discard datapoints
                origsizecheck = double(size(thiscopy.data))
                mask = thiscopy.random_mask(thiscopy.fit_axis,threshold = swap_out)
                thiscopy.data = thiscopy.data[mask]
                derr = thiscopy.get_error()
                x = thiscopy.getaxis(thiscopy.fit_axis)
                x = x[mask] # note that x is probably no longer a pointer
                derr = derr[mask]
                #print 'DEBUG: size of data after cut',double(size(thiscopy.data))/origsizecheck,' (expected ',1.-swap_out,')'
                #}}}
                #{{{ now extend
                number_to_replace = origsizecheck - thiscopy.data.size
                #print 'DEBUG: number_to_replace',number_to_replace
                random_indeces = int32((rand(number_to_replace)*(thiscopy.data.size-1.0)).round())
                thiscopy.data = r_[thiscopy.data,thiscopy.data.copy()[random_indeces]]
                thiscopy.labels([thiscopy.fit_axis],[r_[x,x.copy()[random_indeces]]])
                thiscopy.set_error(r_[derr,derr.copy()[random_indeces]])
                #print 'DEBUG: size of data after extension',double(size(thiscopy.data))/origsizecheck
                #}}}
                try:
                    thiscopy.fit()
                    success = True
                    if len(minbounds) > 0:
                        for k,v in minbounds.iteritems():
                            if thiscopy.output(k) < v:
                                success = False
                    if len(maxbounds) > 0:
                        for k,v in maxbounds.iteritems():
                            if thiscopy.output(k) > v:
                                success = False
                except:
                    #print 'WARNING, didn\'t fit'
                    success = False
                # here, use the internal routines, in case there are constraints, etc
                if success is True:
                    for name in thiscopy.symbol_list: # loop over all fit coeff
                        recordlist[runno][name] = thiscopy.output(name)
        print r'\end{verbatim}'
        return recordlist # collect into a single recordlist array
#}}}
