#AUTOGENERATED! DO NOT EDIT! File to edit: dev/01_core.ipynb (unless otherwise specified).

__all__ = ['defaults', 'PrePostInitMeta', 'BaseObj', 'NewChkMeta', 'BypassNewMeta', 'patch_to', 'patch',
           'patch_property', 'use_kwargs', 'delegates', 'methods_kwargs', 'chk', 'tensor', 'add_docs', 'docs',
           'custom_dir', 'coll_repr', 'GetAttr', 'delegate_attr', 'L', 'ifnone', 'get_class', 'mk_class', 'wrap_class',
           'noop', 'noops', 'set_seed', 'store_attr', 'TensorBase', 'retain_type', 'retain_types', 'tuplify',
           'replicate', 'uniqueify', 'setify', 'is_listy', 'range_of', 'mask2idxs', 'merge', 'shufflish', 'IterLen',
           'ReindexCollection', 'lt', 'gt', 'le', 'ge', 'eq', 'ne', 'add', 'sub', 'mul', 'truediv', 'Inf', 'true',
           'stop', 'gen', 'chunked', 'concat', 'Chunks', 'apply', 'to_detach', 'to_half', 'to_float', 'default_device',
           'to_device', 'to_cpu', 'item_find', 'find_device', 'find_bs', 'compose', 'maps', 'mapper', 'partialler',
           'sort_by_run', 'round_multiple', 'num_cpus', 'add_props', 'make_cross_image', 'show_title', 'show_image',
           'show_titled_image', 'show_image_batch', 'one_hot', 'all_union', 'all_disjoint', 'camel2snake',
           'trainable_params', 'bn_bias_params', 'PrettyString', 'flatten_check', 'display_df', 'one_param']

from .test import *
from .imports import *
from .notebook.showdoc import show_doc

torch.cuda.set_device(int(os.environ.get('DEFAULT_GPU') or 0))

defaults = SimpleNamespace()

class PrePostInitMeta(type):
    "A metaclass that calls optional `__pre_init__` and `__post_init__` methods"
    def __new__(cls, name, bases, dct):
        x = super().__new__(cls, name, bases, dct)
        def _pass(self, *args,**kwargs): pass
        for o in ('__init__', '__pre_init__', '__post_init__'):
            if not hasattr(x,o): setattr(x,o,_pass)
        old_init = x.__init__

        @functools.wraps(old_init)
        def _init(self,*args,**kwargs):
            self.__pre_init__()
            old_init(self, *args,**kwargs)
            self.__post_init__()
        setattr(x, '__init__', _init)
        return x

class BaseObj(metaclass=PrePostInitMeta):
    "Base class that provides `PrePostInitMeta` metaclass to subclasses"
    pass

class NewChkMeta(PrePostInitMeta):
    "Metaclass to avoid recreating object passed to constructor (plus all `PrePostInitMeta` functionality)"
    def __new__(cls, name, bases, dct):
        x = super().__new__(cls, name, bases, dct)
        old_init,old_new = x.__init__,x.__new__

        @functools.wraps(old_init)
        def _new(cls, x=None, *args, **kwargs):
            if x is not None and isinstance(x,cls):
                x._newchk = 1
                return x
            res = old_new(cls)
            res._newchk = 0
            return res

        @functools.wraps(old_init)
        def _init(self,*args,**kwargs):
            if self._newchk: return
            old_init(self, *args, **kwargs)

        x.__init__,x.__new__ = _init,_new
        return x

class BypassNewMeta(type):
    "Metaclass: casts `x` to this class, initializing with `_new_meta` if available"
    def __call__(cls, x, *args, **kwargs):
        if hasattr(cls, '_new_meta'): x = cls._new_meta(x, *args, **kwargs)
        if cls!=x.__class__: x.__class__ = cls
        return x

def patch_to(cls, as_prop=False):
    "Decorator: add `f` to `cls`"
    def _inner(f):
        nf = copy(f)
        # `functools.update_wrapper` when passing patched function to `Pipeline`, so we do it manually
        for o in functools.WRAPPER_ASSIGNMENTS: setattr(nf, o, getattr(f,o))
        nf.__qualname__ = f"{cls.__name__}.{f.__name__}"
        setattr(cls, f.__name__, property(nf) if as_prop else nf)
        return f
    return _inner

def patch(f):
    "Decorator: add `f` to the first parameter's class (based on f's type annotations)"
    cls = next(iter(f.__annotations__.values()))
    return patch_to(cls)(f)

def patch_property(f):
    "Decorator: add `f` as a property to the first parameter's class (based on f's type annotations)"
    cls = next(iter(f.__annotations__.values()))
    return patch_to(cls, as_prop=True)(f)

def _mk_param(n,d=None): return inspect.Parameter(n, inspect.Parameter.KEYWORD_ONLY, default=d)

def use_kwargs(names, keep=False):
    "Decorator: replace `**kwargs` in signature with `names` params"
    def _f(f):
        sig = inspect.signature(f)
        sigd = dict(sig.parameters)
        k = sigd.pop('kwargs')
        s2 = {n:_mk_param(n) for n in names if n not in sigd}
        sigd.update(s2)
        if keep: sigd['kwargs'] = k
        f.__signature__ = sig.replace(parameters=sigd.values())
        return f
    return _f

def delegates(to=None, keep=False):
    "Decorator: replace `**kwargs` in signature with params from `to`"
    def _f(f):
        if to is None: to_f,from_f = f.__base__.__init__,f.__init__
        else:          to_f,from_f = to,f
        sig = inspect.signature(from_f)
        sigd = dict(sig.parameters)
        k = sigd.pop('kwargs')
        s2 = {k:v for k,v in inspect.signature(to_f).parameters.items()
              if v.default != inspect.Parameter.empty and k not in sigd}
        sigd.update(s2)
        if keep: sigd['kwargs'] = k
        from_f.__signature__ = sig.replace(parameters=sigd.values())
        return f
    return _f

def methods_kwargs(cls):
    "Replace methods in `self._methods` with those from `kwargs`"
    old_init = cls.__init__
    def _init(self, *args, **kwargs):
        for k in cls._methods:
            if k in kwargs: setattr(self, k, types.MethodType(kwargs.pop(k), self))
        old_init(self, *args, **kwargs)
    cls.__init__ = use_kwargs(cls._methods)(_init)
    return cls

#NB: Please don't move this to a different line or module, since it's used in testing `get_source_link`
def chk(f): return typechecked(always=True)(f)

#NB: Please don't move this to a different line or module, since it's used in testing `get_source_link`
@patch
def ls(self:Path):
    "Contents of path as a list"
    return list(self.iterdir())

def tensor(x, *rest, **kwargs):
    "Like `torch.as_tensor`, but handle lists too, and can pass multiple vector elements directly."
    if len(rest): x = (x,)+rest
    # Pytorch bug in dataloader using num_workers>0
    if isinstance(x, (tuple,list)) and len(x)==0: return tensor(0)
    res = (torch.tensor(x, **kwargs) if isinstance(x, (tuple,list))
           else as_tensor(x, **kwargs) if hasattr(x, '__array__')
           else as_tensor(x, **kwargs) if is_listy(x)
           else as_tensor(x, **kwargs) if is_iter(x)
           else None)
    if res is None:
        res = as_tensor(array(x), **kwargs)
        if res.dtype is torch.float64: return res.float()
    if res.dtype is torch.int32:
        warn('Tensor is int32: upgrading to int64; for better performance use int64 input')
        return res.long()
    return res

def add_docs(cls, cls_doc=None, **docs):
    "Copy values from `docs` to `cls` docstrings, and confirm all public methods are documented"
    if cls_doc is not None: cls.__doc__ = cls_doc
    for k,v in docs.items():
        f = getattr(cls,k)
        if hasattr(f,'__func__'): f = f.__func__ # required for class methods
        f.__doc__ = v
    # List of public callables without docstring
    nodoc = [c for n,c in vars(cls).items() if isinstance(c,Callable)
             and not n.startswith('_') and c.__doc__ is None]
    assert not nodoc, f"Missing docs: {nodoc}"
    assert cls.__doc__ is not None, f"Missing class docs: {cls}"

def docs(cls):
    "Decorator version of `add_docs`, using `_docs` dict"
    add_docs(cls, **cls._docs)
    return cls

def custom_dir(c, add:List):
    "Implement custom `__dir__`, adding `add` to `cls`"
    return dir(type(c)) + list(c.__dict__.keys()) + add

def coll_repr(c, max=1000):
    "String repr of up to `max` items of (possibly lazy) collection `c`"
    return f'(#{len(c)}) [' + ','.join(itertools.islice(map(str,c), 10)) + ('...'
            if len(c)>10 else '') + ']'

class GetAttr(BaseObj):
    "Inherit from this to have all attr accesses in `self._xtra` passed down to `self.default`"
    @property
    def _xtra(self): return [o for o in dir(self.default) if not o.startswith('_')]
    def __getattr__(self,k):
        if k in self._xtra: return getattr(self.default, k)
        raise AttributeError(k)
    def __dir__(self): return custom_dir(self, self._xtra)

def delegate_attr(self, k, to):
    "Use in `__getattr__` to delegate to attr `to` without inheriting from `GetAttr`"
    if k.startswith('_') or k==to: raise AttributeError(k)
    try: return getattr(getattr(self,to), k)
    except AttributeError: raise AttributeError(k) from None

def _mask2idxs(mask):
    mask = list(mask)
    if len(mask)==0: return []
    if isinstance(mask[0],bool): return [i for i,m in enumerate(mask) if m]
    return [int(i) for i in mask]

def _listify(o):
    if o is None: return []
    if isinstance(o, list): return o
    if isinstance(o, (str,np.ndarray,Tensor)): return [o]
    if is_iter(o): return list(o)
    return [o]

class L(GetAttr, metaclass=NewChkMeta):
    "Behaves like a list of `items` but can also index with list of indices or masks"
    _xtra =  [o for o in dir([]) if not o.startswith('_')]

    def __init__(self, items=None, *rest, use_list=False, match=None):
        if rest: items = (items,)+rest
        if items is None: items = []
        self.items = self.default = list(items) if use_list else _listify(items)
        if match is not None:
            if len(self.items)==1: self.items = self.items*len(match)
            else: assert len(self.items)==len(match), 'Match length mismatch'

    def __len__(self): return len(self.items)
    def __delitem__(self, i): del(self.items[i])
    def __repr__(self): return f'{coll_repr(self)}'
    def __eq__(self,b): return all_equal(b,self)
    def __iter__(self): return (self[i] for i in range(len(self)))
    def __invert__(self): return L(not i for i in self)
    def __mul__ (a,b): return L(a.items*b)
    def __add__ (a,b): return L(a.items+_listify(b))
    def __radd__(a,b): return L(b)+a
    def __addi__(a,b):
        a.items += list(b)
        return a

    def __getitem__(self, idx):
        "Retrieve `idx` (can be list of indices, or mask, or int) items"
        return L(self.items[i] for i in _mask2idxs(idx)) if is_iter(idx) else self.items[idx]

    def __setitem__(self, idx, o):
        "Set `idx` (can be list of indices, or mask, or int) items to `o` (which is broadcast if not iterable)"
        idx = idx if isinstance(idx,L) else _listify(idx)
        if not is_iter(o): o = [o]*len(idx)
        for i,o_ in zip(idx,o): self.items[i] = o_

    def sorted(self, key=None, reverse=False):
        "New `L` sorted by `key`. If key is str then use `attrgetter`. If key is int then use `itemgetter`."
        if isinstance(key,str):   k=lambda o:getattr(o,key,0)
        elif isinstance(key,int): k=itemgetter(key)
        else: k=key
        return L(sorted(self.items, key=k, reverse=reverse))

    @classmethod
    def range(self, a, b=None, step=None):
        "Same as builtin `range`, but returns an `L`. Can pass a collection for `a`, to use `len(a)`"
        if is_coll(a): a = len(a)
        return L(range(a,b,step)) if step is not None else L(range(a,b)) if b is not None else L(range(a))

    def zipped(self):         return L(zip(*self))
    def zipwith(self, *rest): return L(zip(self, *rest))
    def itemgot(self, idx):   return self.mapped(itemgetter(idx))
    def attrgot(self, k):     return self.mapped(lambda o:getattr(o,k,0))
    def tensored(self):       return self.mapped(tensor)
    def stack(self, dim=0):   return torch.stack(list(self.tensored()), dim=dim)
    def cat  (self, dim=0):   return torch.cat  (list(self.tensored()), dim=dim)
    def cycle(self):          return itertools.cycle(self) if len(self) > 0 else itertools.cycle([None])
    def mapped(self, f, *args, **kwargs): return L(map(partial(f,*args,**kwargs), self))
    def shuffled(self):
        it = copy(self.items)
        random.shuffle(it)
        return L(it)

def ifnone(a, b):
    "`b` if `a` is None else `a`"
    return b if a is None else a

def get_class(nm, *fld_names, sup=None, doc=None, funcs=None, **flds):
    "Dynamically create a class, optionally inheriting from `sup`, containing `fld_names`"
    attrs = {}
    for f in fld_names: attrs[f] = None
    for f in L(funcs): attrs[f.__name__] = f
    for k,v in flds.items(): attrs[k] = v
    sup = ifnone(sup, ())
    if not isinstance(sup, tuple): sup=(sup,)

    def _init(self, *args, **kwargs):
        for i,v in enumerate(args): setattr(self, list(attrs.keys())[i], v)
        for k,v in kwargs.items(): setattr(self,k,v)

    def _repr(self):
        return '\n'.join(f'{o}: {getattr(self,o)}' for o in set(dir(self))
                         if not o.startswith('_') and not isinstance(getattr(self,o), types.MethodType))

    if not sup: flds['__repr__'] = _repr
    attrs['__init__'] = _init
    res = type(nm, sup, attrs)
    if doc is not None: res.__doc__ = doc
    return res

def mk_class(nm, *fld_names, sup=None, doc=None, funcs=None, mod=None, **flds):
    "Create a class using `get_class` and add to the caller's module"
    if mod is None: mod = inspect.currentframe().f_back.f_locals
    res = get_class(nm, *fld_names, sup=sup, doc=doc, funcs=funcs, **flds)
    mod[nm] = res

def wrap_class(nm, *fld_names, sup=None, doc=None, funcs=None, **flds):
    "Decorator: makes function a method of a new class `nm` passing parameters to `mk_class`"
    def _inner(f):
        mk_class(nm, *fld_names, sup=sup, doc=doc, funcs=L(funcs)+f, mod=f.__globals__, **flds)
        return f
    return _inner

def noop (x=None, *args, **kwargs):
    "Do nothing"
    return x

def noops(self, x=None, *args, **kwargs):
    "Do nothing (method)"
    return x

def set_seed(s):
    "Set random seed for `random`, `torch`, and `numpy` (where available)"
    try: torch.manual_seed(s)
    except NameError: pass
    try: np.random.seed(s%(2**32-1))
    except NameError: pass
    random.seed(s)

def store_attr(self, nms):
    "Store params named in comma-separated `nms` from calling context into attrs in `self`"
    mod = inspect.currentframe().f_back.f_locals
    for n in nms.split(','): setattr(self,n,mod[n])

class TensorBase(Tensor, metaclass=BypassNewMeta):
    def _new_meta(self, *args, **kwargs): return tensor(self)

def _patch_tb():
    def get_f(fn):
        def _f(self, *args, **kwargs):
            cls = self.__class__
            res = getattr(super(TensorBase, self), fn)(*args, **kwargs)
            return cls(res) if isinstance(res,Tensor) else res
        return _f

    t = tensor([1])
    skips = '__class__ __deepcopy__ __delattr__ __dir__ __doc__ __getattribute__ __hash__ __init__ \
        __init_subclass__ __new__ __reduce__ __module__ __setstate__'.split()

    for fn in dir(t):
        if fn in skips: continue
        f = getattr(t, fn)
        if isinstance(f, (types.MethodWrapperType, types.BuiltinFunctionType, types.BuiltinMethodType, types.MethodType, types.FunctionType)):
            setattr(TensorBase, fn, get_f(fn))

_patch_tb()

def retain_type(new, old, typ=None):
    "Cast `new` to type of `old` if it's a superclass"
    if not typ:
        # e.g. old is TensorImage, new is Tensor - if not subclass then do nothing
        if not isinstance(old, type(new)): return new
        typ = type(old)
    # Do nothing the new type is already an instance of requested type (i.e. same type)
    return typ(new) if typ!=NoneType and not isinstance(new, typ) else new

def retain_types(new, old):
    "Cast each item of `new` to type of matching item in `old` if it's a superclass"
    if not is_listy(old): old = itertools.cycle([old])
    return tuple(itertools.starmap(retain_type, zip(new,old)))

def tuplify(o, use_list=False, match=None):
    "Make `o` a tuple"
    return tuple(L(o, use_list=use_list, match=match))

def replicate(item,match):
    "Create tuple of `item` copied `len(match)` times"
    return (item,)*len(match)

def uniqueify(x, sort=False, bidir=False, start=None):
    "Return the unique elements in `x`, optionally `sort`-ed, optionally return the reverse correspondance."
    res = list(OrderedDict.fromkeys(x).keys())
    if start is not None: res = L(start)+res
    if sort: res.sort()
    if bidir: return res, {v:k for k,v in enumerate(res)}
    return res

def setify(o): return o if isinstance(o,set) else set(L(o))

def is_listy(x):
    "`isinstance(x, (tuple,list,L))`"
    return isinstance(x, (tuple,list,L,slice,Generator))

def range_of(x):
    "All indices of collection `x` (i.e. `list(range(len(x)))`)"
    return list(range(len(x)))

def mask2idxs(mask):
    "Convert bool mask or index list to index `L`"
    return L(_mask2idxs(mask))

def merge(*ds):
    "Merge all dictionaries in `ds`"
    return {k:v for d in ds for k,v in d.items()}

def shufflish(x, pct=0.04):
    "Randomly relocate items of `x` up to `pct` of `len(x)` from their starting location"
    n = len(x)
    return L(x[i] for i in sorted(range_of(x), key=lambda o: o+n*(1+random.random()*pct)))

class IterLen:
    "Base class to add iteration to anything supporting `len` and `__getitem__`"
    def __iter__(self): return (self[i] for i in range_of(self))

@docs
class ReindexCollection(GetAttr, IterLen):
    "Reindexes collection `coll` with indices `idxs` and optional LRU cache of size `cache`"
    def __init__(self, coll, idxs=None, cache=None):
        self.default,self.coll,self.idxs,self.cache = coll,coll,ifnone(idxs,L.range(coll)),cache
        def _get(self, i): return self.coll[i]
        self._get = types.MethodType(_get,self)
        if cache is not None: self._get = functools.lru_cache(maxsize=cache)(self._get)

    def __getitem__(self, i): return self._get(self.idxs[i])
    def __len__(self): return len(self.coll)
    def reindex(self, idxs): self.idxs = idxs
    def shuffle(self): random.shuffle(self.idxs)
    def cache_clear(self): self._get.cache_clear()

    _docs = dict(reindex="Replace `self.idxs` with idxs",
                shuffle="Randomly shuffle indices",
                cache_clear="Clear LRU cache")

def _oper(op,a,b=None): return (lambda o:op(o,a)) if b is None else op(a,b)

def _mk_op(nm, mod=None):
    "Create an operator using `oper` and add to the caller's module"
    if mod is None: mod = inspect.currentframe().f_back.f_locals
    op = getattr(operator,nm)
    def _inner(a,b=None): return _oper(op, a,b)
    _inner.__name__ = _inner.__qualname__ = nm
    _inner.__doc__ = f'Same as `operator.{nm}`, or returns partial if 1 arg'
    mod[nm] = _inner

for op in 'lt gt le ge eq ne add sub mul truediv'.split(): _mk_op(op)

class _InfMeta(type):
    @property
    def count(self): return itertools.count()
    @property
    def zeros(self): return itertools.cycle([0])
    @property
    def ones(self):  return itertools.cycle([1])
    @property
    def nones(self): return itertools.cycle([None])

class Inf(metaclass=_InfMeta):
    "Infinite lists"
    pass

def true(*args, **kwargs):
    "Predicate: always `True`"
    return True

def stop(e=StopIteration):
    "Raises exception `e` (by default `StopException`) even if in an expression"
    raise e

def gen(func, seq, cond=true):
    "Like `(func(o) for o in seq if cond(func(o)))` but handles `StopIteration`"
    return itertools.takewhile(cond, map(func,seq))

def chunked(it, cs, drop_last=False):
    if not isinstance(it, Iterator): it = iter(it)
    while True:
        res = list(itertools.islice(it, cs))
        if res and (len(res)==cs or not drop_last): yield res
        if len(res)<cs: return

def concat(*ls):
    "Concatenate tensors, arrays, lists, or tuples"
    if not len(ls): return []
    it = ls[0]
    return retain_type(torch.cat(ls) if isinstance(it,torch.Tensor)
            else np.concatenate(ls) if isinstance(it,ndarray)
            else sum(ls,[]) if isinstance(it,list)
            else sum(ls,()) if isinstance(it,tuple)
            else stop(TypeError), it)

class Chunks:
    "Slice and int indexing into a list of lists"
    def __init__(self, chunks, lens=None):
        self.chunks = chunks
        self.lens = L(map(len,self.chunks) if lens is None else lens)
        self.cumlens = np.cumsum(0+self.lens)
        self.totlen = self.cumlens[-1]

    def __getitem__(self,i):
        if isinstance(i,slice): return self.getslice(i)
        di,idx = self.doc_idx(i)
        return self.chunks[di][idx]

    def getslice(self, i):
        st_d,st_i = self.doc_idx(ifnone(i.start,0))
        en_d,en_i = self.doc_idx(ifnone(i.stop,self.totlen+1))
        res = [self.chunks[st_d][st_i:(en_i if st_d==en_d else sys.maxsize)]]
        for b in range(st_d+1,en_d): res.append(self.chunks[b])
        if st_d!=en_d and en_d<len(self.chunks): res.append(self.chunks[en_d][:en_i])
        return concat(*res)

    def doc_idx(self, i):
        if i<0: i=self.totlen+i # count from end
        docidx = np.searchsorted(self.cumlens, i+1)-1
        cl = self.cumlens[docidx]
        return docidx,i-cl

def apply(func, x, *args, **kwargs):
    "Apply `func` recursively to `x`, passing on args"
    if is_listy(x): return type(x)(apply(func, o, *args, **kwargs) for o in x)
    if isinstance(x,dict):  return {k: apply(func, v, *args, **kwargs) for k,v in x.items()}
    return retain_type(func(x, *args, **kwargs), x)

def to_detach(b, cpu=True):
    "Recursively detach lists of tensors in `b `; put them on the CPU if `cpu=True`."
    def _inner(x, cpu=True):
        if not isinstance(x,Tensor): return x
        x = x.detach()
        return x.cpu() if cpu else x
    return apply(_inner, b, cpu=cpu)

def to_half(b):
    "Recursively map lists of tensors in `b ` to FP16."
    return apply(lambda x: x.half() if torch.is_floating_point(x) else x, b)

def to_float(b):
    "Recursively map lists of int tensors in `b ` to float."
    return apply(lambda x: x.float() if torch.is_floating_point(x) else x, b)

# None: True if available; True: error if not availabe; False: use CPU
defaults.use_cuda = None

def default_device(use_cuda=-1):
    "Return or set default device; `use_cuda`: None - CUDA if available; True - error if not availabe; False - CPU"
    if use_cuda != -1: defaults.use_cuda=use_cuda
    use = defaults.use_cuda or (torch.cuda.is_available() and defaults.use_cuda is None)
    assert torch.cuda.is_available() or not use
    return torch.device(torch.cuda.current_device()) if use else torch.device('cpu')

def to_device(b, device=None):
    "Recursively put `b` on `device`."
    if device is None: device=default_device()
    def _inner(o): return o.to(device, non_blocking=True) if isinstance(o,Tensor) else o
    return apply(_inner, b)

def to_cpu(b):
    "Recursively map lists of tensors in `b ` to the cpu."
    return to_device(b,'cpu')

def item_find(x, idx=0):
    "Recursively takes the `idx`-th element of `x`"
    if is_listy(x): return item_find(x[idx])
    if isinstance(x,dict):
        key = list(x.keys())[idx] if isinstance(idx, int) else idx
        return item_find(x[key])
    return x

def find_device(b):
    "Recursively search the device of `b`."
    return item_find(b).device

def find_bs(b):
    "Recursively search the batch size of `b`."
    return item_find(b).shape[0]

def compose(*funcs, order=None):
    "Create a function that composes all functions in `funcs`, passing along remaining `*args` and `**kwargs` to all"
    funcs = L(funcs)
    if order is not None: funcs = funcs.sorted(order)
    def _inner(x, *args, **kwargs):
        for f in L(funcs): x = f(x, *args, **kwargs)
        return x
    return _inner

def maps(*args, retain=noop):
    "Like `map`, except funcs are composed first"
    f = compose(*args[:-1])
    def _f(b): return retain(f(b), b)
    return map(_f, args[-1])

def mapper(f):
    "Create a function that maps `f` over an input collection"
    return lambda o: [f(o_) for o_ in o]

def partialler(f, *args, order=None, **kwargs):
    "Like `functools.partial` but also copies over docstring"
    fnew = partial(f,*args,**kwargs)
    fnew.__doc__ = f.__doc__
    if order is not None: fnew.order=order
    elif hasattr(f,'order'): fnew.order=f.order
    return fnew

def _is_instance(f, gs):
    tst = [g if type(g) in [type, 'function'] else g.__class__ for g in gs]
    for g in tst:
        if isinstance(f, g) or f==g: return True
    return False

def _is_first(f, gs):
    for o in L(getattr(f, 'run_after', None)):
        if _is_instance(o, gs): return False
    for g in gs:
        if _is_instance(f, L(getattr(g, 'run_before', None))): return False
    return True

def sort_by_run(fs):
    end = L(getattr(f, 'toward_end', False) for f in fs)
    inp,res = L(fs)[~end] + L(fs)[end], []
    while len(inp) > 0:
        for i,o in enumerate(inp):
            if _is_first(o, inp):
                res.append(inp.pop(i))
                break
        else: raise Exception("Impossible to sort")
    return res

def round_multiple(x, mult, round_down=False):
    "Round `x` to nearest multiple of `mult`"
    def _f(x_): return (int if round_down else round)(x_/mult)*mult
    res = L(x).mapped(_f)
    return res if is_listy(x) else res[0]

def num_cpus():
    "Get number of cpus"
    try:                   return len(os.sched_getaffinity(0))
    except AttributeError: return os.cpu_count()

defaults.cpus = min(16, num_cpus())

def add_props(f, n=2):
    "Create properties passing each of `range(n)` to f"
    return (property(partial(f,i)) for i in range(n))

def make_cross_image(bw=True):
    "Create a tensor containing a cross image, either `bw` (True) or color"
    if bw:
        im = torch.zeros(5,5)
        im[2,:] = 1.
        im[:,2] = 1.
    else:
        im = torch.zeros(3,5,5)
        im[0,2,:] = 1.
        im[1,:,2] = 1.
    return im

def show_title(o, ax=None, ctx=None, label=None, **kwargs):
    "Set title of `ax` to `o`, or print `o` if `ax` is `None`"
    ax = ifnone(ax,ctx)
    if ax is None: print(o)
    elif hasattr(ax, 'set_title'): ax.set_title(o)
    elif isinstance(ax, pd.Series):
        while label in ax: label += '_'
        ax = ax.append(pd.Series({label: o}))
    return ax

def show_image(im, ax=None, figsize=None, title=None, ctx=None, **kwargs):
    "Show a PIL or PyTorch image on `ax`."
    ax = ifnone(ax,ctx)
    if ax is None: _,ax = plt.subplots(figsize=figsize)
    # Handle pytorch axis order
    if isinstance(im,Tensor):
        im = to_cpu(im)
        if im.shape[0]<5: im=im.permute(1,2,0)
    elif not isinstance(im,np.ndarray): im=array(im)
    # Handle 1-channel images
    if im.shape[-1]==1: im=im[...,0]
    ax.imshow(im, **kwargs)
    if title is not None: ax.set_title(title)
    ax.axis('off')
    return ax

def show_titled_image(o, **kwargs):
    "Call `show_image` destructuring `o` to `(img,title)`"
    show_image(o[0], title=str(o[1]), **kwargs)

def show_image_batch(b, show=show_titled_image, items=9, cols=3, figsize=None, **kwargs):
    "Display batch `b` in a grid of size `items` with `cols` width"
    rows = (items+cols-1) // cols
    if figsize is None: figsize = (cols*3, rows*3)
    fig,axs = plt.subplots(rows, cols, figsize=figsize)
    for *o,ax in zip(*to_cpu(b), axs.flatten()): show(o, ax=ax, **kwargs)

#Comes from 05_data_core.ipynb.
def one_hot(x, c):
    "One-hot encode `x` with `c` classes."
    res = torch.zeros(c, dtype=torch.uint8)
    res[L(x)] = 1.
    return res

#Comes from 06_data_source.ipynb.
def all_union(sets):
    "Set of union of all `sets` (each `setified` if needed)"
    return set().union(*(map(setify,sets)))

#Comes from 06_data_source.ipynb.
def all_disjoint(sets):
    "`True` iif no element appears in more than one item of `sets`"
    return sum(map(len,sets))==len(all_union(sets))

#Comes from 13_learner.ipynb.
_camel_re1 = re.compile('(.)([A-Z][a-z]+)')
_camel_re2 = re.compile('([a-z0-9])([A-Z])')

def camel2snake(name):
    s1   = re.sub(_camel_re1, r'\1_\2', name)
    return re.sub(_camel_re2, r'\1_\2', s1).lower()

#Comes from 13_learner.ipynb.
def trainable_params(m):
    "Return all trainable parameters of `m`"
    return [p for p in m.parameters() if p.requires_grad]

#Comes from 13_learner.ipynb.
def bn_bias_params(m):
    "Return all bias and BatchNorm parameters"
    if isinstance(m, (nn.BatchNorm1d, nn.BatchNorm2d, nn.BatchNorm3d)):
        return list(m.parameters())
    res = sum([bn_bias_params(c) for c in m.children()], [])
    if hasattr(m, 'bias'): res.append(m.bias)
    return res

#Comes from 15_callback_hook.ipynb.
class PrettyString(str):
    "Little hack to get strings to show properly in Jupyter."
    def __repr__(self): return self

#Comes from 20_metrics.ipynb.
def flatten_check(inp, targ, detach=True):
    "Check that `out` and `targ` have the same number of elements and flatten them."
    inp,targ = to_detach(inp.contiguous().view(-1)),to_detach(targ.contiguous().view(-1))
    test_eq(len(inp), len(targ))
    return inp,targ

#Comes from 31_text_data.ipynb.
def display_df(df):
    "Display `df` in a notebook or defaults to print"
    try:
        from IPython.display import display, HTML
        display(HTML(df.to_html()))
    except: print(df)

#Comes from 32_text_models_awdlstm.ipynb.
def one_param(m): return next(iter(m.parameters()))