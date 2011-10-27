#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Main module code templates

"""

global_copyright = """\
// Generated code for Python source for module '%(name)s'
// created by Nuitka version %(version)s

// This code is in part copyright Kay Hayen, license GPLv3. This has the consequence that
// your must either obtain a commercial license or also publish your original source code
// under the same license unless you don't distribute this source or its binary.
"""

module_inittab_entry = """\
{ (char *)"%(module_name)s", init%(module_identifier)s },"""

main_program = """\
// Our own inittab for lookup of "frozen" modules, i.e. the ones included in this binary.
static struct _inittab _module_inittab[] =
{
%(module_inittab)s
    { NULL, NULL }
};

#ifdef _NUITKA_EXE

static PyObject *_loader_frozen_modules = NULL;

#define _DEBUG_UNFREEZER 0

static PyObject *_PATH_UNFREEZER_FIND_MODULE( PyObject *self, PyObject *args )
{
    PyObject *module_name;

    if ( PyTuple_Check( args ))
    {
       assert( PyTuple_Size( args ) == 2 );

       module_name = PyTuple_GetItem( args, 0 );
    }
    else
    {
       assert( PyString_Check( args ) );

       module_name = args;
    }

    char *name = PyString_AsString( module_name );

#if _DEBUG_UNFREEZER
    printf( "Looking for %%s\\n", name );
#endif

    struct _inittab *current = _module_inittab;

    while ( current->name != NULL )
    {
       if ( strcmp( name, current->name ) == 0 )
       {
           return INCREASE_REFCOUNT( _loader_frozen_modules );
       }

       current++;
    }

#if _DEBUG_UNFREEZER
    printf( "Didn't find %%s\\n", name );
#endif

    return INCREASE_REFCOUNT( Py_None );
}

static PyObject *_PATH_UNFREEZER_LOAD_MODULE( PyObject *self, PyObject *args )
{
    PyObject *module_name = args;
    assert( module_name );

    char *name = PyString_AsString( module_name );

    struct _inittab *current = _module_inittab;

    while ( current->name != NULL )
    {
       if ( strcmp( name, current->name ) == 0 )
       {
#if _DEBUG_UNFREEZER
           printf( "Loading %%s\\n", name );
#endif
           current->initfunc();

           PyObject *sys_modules = PySys_GetObject( (char *)"modules" );

#if _DEBUG_UNFREEZER
           printf( "Loaded %%s\\n", name );
#endif

           return LOOKUP_SUBSCRIPT( sys_modules, module_name );
       }

       current++;
    }

    assert( false );

    return INCREASE_REFCOUNT( Py_None );
}


static PyMethodDef _method_def_loader_find_module
{
    "find_module",
    _PATH_UNFREEZER_FIND_MODULE,
    METH_OLDARGS,
    NULL
};

static PyMethodDef _method_def_loader_load_module
{
    "load_module",
    _PATH_UNFREEZER_LOAD_MODULE,
    METH_OLDARGS,
    NULL
};

static void REGISTER_META_PATH_UNFREEZER( void )
{
    PyObject *method_dict = PyDict_New();

    assertObject( method_dict );

    PyObject *loader_find_module = PyCFunction_New( &_method_def_loader_find_module, NULL );
    assertObject( loader_find_module );
    PyDict_SetItemString( method_dict, "find_module", loader_find_module );

    PyObject *loader_load_module = PyCFunction_New( &_method_def_loader_load_module, NULL );
    assertObject( loader_load_module );
    PyDict_SetItemString( method_dict, "load_module", loader_load_module );

    _loader_frozen_modules = PyObject_CallFunctionObjArgs(
        (PyObject *)&PyClass_Type,
        PyString_FromString( "_nuitka_compiled_modules_loader" ),
        _python_tuple_empty,
        method_dict,
        NULL
    );

    assertObject( _loader_frozen_modules );

    int res = PyList_Insert( PySys_GetObject( ( char *)"meta_path" ), 0, _loader_frozen_modules );

    assert( res == 0 );
}

#endif

// The main program for C++. It needs to prepare the interpreter and then calls the
// initialization code of the __main__ module.

int main( int argc, char *argv[] )
{

    Py_Initialize();
    PySys_SetArgv( argc, argv );

    // Initialize the constant values used.
    _initConstants();

    // Initialize the compiled types of Nuitka.
    PyType_Ready( &Nuitka_Generator_Type );
    PyType_Ready( &Nuitka_Function_Type );
    PyType_Ready( &Nuitka_Method_Type );
    PyType_Ready( &Nuitka_Genexpr_Type );

    enhancePythonTypes();

    // Register the initialization functions for modules included in the binary if any
    int res = PyImport_ExtendInittab( _module_inittab );
    assert( res != -1 );

    // Set the sys.executable path to the original Python executable on Linux
    // or to python.exe on Windows.
    PySys_SetObject( (char *)"executable", PyString_FromString( %(sys_executable)s ) );

    REGISTER_META_PATH_UNFREEZER();

    init__main__();

    if ( PyErr_Occurred() )
    {
        PyErr_Print();
        return 1;
    }
    else
    {
        return 0;
    }
}
"""

module_header_template = """\

#include <nuitka/helpers.hpp>

NUITKA_MODULE_INIT_FUNCTION init%(module_identifier)s(void);

extern PyObject *_module_%(module_identifier)s;

class PyObjectGlobalVariable_%(module_identifier)s
{
    public:
        explicit PyObjectGlobalVariable_%(module_identifier)s( PyObject **dummy, PyObject **var_name )
        {
            assert( var_name );

            this->var_name   = (PyStringObject **)var_name;
        }

        PyObject *asObject0() const
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY( (PyModuleObject *)_module_%(module_identifier)s, *this->var_name );

            if (likely( entry->me_value != NULL ))
            {
                assert( entry->me_value->ob_refcnt > 0 );

                return entry->me_value;
            }

            entry = GET_PYDICT_ENTRY( _module_builtin, *this->var_name );

            if (likely( entry->me_value != NULL ))
            {
                assert( entry->me_value->ob_refcnt > 0 );

                return entry->me_value;
            }

            PyErr_Format( PyExc_NameError, "global name '%%s' is not defined", Nuitka_String_AsString( (PyObject *)*this->var_name ) );
            throw _PythonException();
        }

        PyObject *asObject() const
        {
            return INCREASE_REFCOUNT( this->asObject0() );
        }

        PyObject *asObject0( PyObject *dict ) const
        {
            PyObject *result = PyDict_GetItem( dict, (PyObject *)*this->var_name );

            if ( result != NULL )
            {
                return result;
            }
            else
            {
                return this->asObject0();
            }
        }

        void assign( PyObject *value ) const
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY( (PyModuleObject *)_module_%(module_identifier)s, *this->var_name );

            // Values are more likely set than not set, in that case speculatively try the
            // quickest access method.
            if (likely( entry->me_value != NULL ))
            {
                PyObject *old = entry->me_value;
                entry->me_value = value;

                Py_DECREF( old );
            }
            else
            {
                DICT_SET_ITEM( ((PyModuleObject *)_module_%(module_identifier)s)->md_dict, (PyObject *)*this->var_name, value );

                Py_DECREF( value );
            }
        }

        void assign0( PyObject *value ) const
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY( (PyModuleObject *)_module_%(module_identifier)s, *this->var_name );

            // Values are more likely set than not set, in that case speculatively try the
            // quickest access method.
            if (likely( entry->me_value != NULL ))
            {
                PyObject *old = entry->me_value;
                entry->me_value = INCREASE_REFCOUNT( value );

                Py_DECREF( old );
            }
            else
            {
                DICT_SET_ITEM( ((PyModuleObject *)_module_%(module_identifier)s)->md_dict, (PyObject *)*this->var_name, value );
            }
        }

        void del() const
        {
            int status = PyDict_DelItem( ((PyModuleObject *)_module_%(module_identifier)s)->md_dict, (PyObject *)*this->var_name );

            if (unlikely( status == -1 ))
            {
                PyErr_Format( PyExc_NameError, "name '%%s' is not defined", Nuitka_String_AsString( (PyObject *)*this->var_name ) );
                throw _PythonException();
            }
        }

        bool isInitialized( bool allow_builtins = true ) const
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY( (PyModuleObject *)_module_%(module_identifier)s, *this->var_name );

            if (likely( entry->me_value != NULL ))
            {
                return true;
            }

            if ( allow_builtins )
            {
                entry = GET_PYDICT_ENTRY( _module_builtin, *this->var_name );

                return entry->me_value != NULL;
            }
            else
            {
                return false;
            }
        }

    private:
        PyStringObject **var_name;
};

"""

module_body_template = """\
#include "nuitka/prelude.hpp"

#include "__modules.hpp"
#include "__constants.hpp"
#include "__reverses.hpp"

// The _module_%(module_identifier)s is a Python object pointer of module type.

// Note: For full compatability with CPython, every module variable access needs to go
// through it except for cases where the module cannot possibly have changed in the mean
// time.

PyObject *_module_%(module_identifier)s;

// The module level variables.
%(module_globals)s

// The module function declarations.
%(module_functions_decl)s

// The module function definitions.
%(module_functions_code)s

%(expression_temp_decl)s

// Frame object of the module.
PyObject *frame_%(module_identifier)s;

// Frame object of the module.
static inline PyObject *frameobj_%(module_identifier)s( void )
{
   return frame_%(module_identifier)s;
}

#ifdef _NUITKA_EXE
static bool init_done = false;
#endif

// The exported interface to CPython. On import of the module, this function gets
// called. It has have that exact function name.

NUITKA_MODULE_INIT_FUNCTION init%(module_identifier)s(void)
{
#ifdef _NUITKA_EXE
    // Packages can be imported recursively in deep executables.
    if ( init_done )
    {
        return;
    }
    else
    {
        init_done = true;
    }
#endif

#ifdef _NUITKA_MODULE
    // In case of a stand alone extension module, need to call initialization the init here
    // because that's how we are going to get called here.

    // Initialize the constant values used.
    _initConstants();

    // Initialize the compiled types of Nuitka.
    PyType_Ready( &Nuitka_Generator_Type );
    PyType_Ready( &Nuitka_Function_Type );
    PyType_Ready( &Nuitka_Method_Type );
    PyType_Ready( &Nuitka_Genexpr_Type );
#endif

    // puts( "in init%(module_identifier)s" );

#ifdef _NUITKA_MODULE
    // Remember it here, Py_InitModule4 will clear it.
    char const *qualified_name = _Py_PackageContext;
#endif

    // Create the module object first. There are no methods initially, all are added
    // dynamically in actual code only.  Also no __doc__ is initially set, as it could not
    // contain 0 this way, added early in actual code.  No self for modules, we have no
    // use for it.
    _module_%(module_identifier)s = Py_InitModule4(
        "%(module_name)s",       // Module Name
        NULL,                    // No methods initially, all are added dynamically in actual code only.
        NULL,                    // No __doc__ is initially set, as it could not contain 0 this way, added early in actual code.
        NULL,                    // No self for modules, we don't use it.
        PYTHON_API_VERSION
    );

    assertObject( _module_%(module_identifier)s );

    frame_%(module_identifier)s = MAKE_FRAME( %(filename_identifier)s, %(module_name_obj)s, _module_%(module_identifier)s );

    // Initialize the standard module attributes.
%(module_inits)s

    // For deep importing of a module we need to have "__builtins__", so we set it
    // ourselves in the same way than CPython does.

    PyObject *module_dict = PyModule_GetDict( _module_%(module_identifier)s );

    if ( PyDict_GetItemString( module_dict, "__builtins__") == NULL )
    {
#ifndef __NUITKA_NO_ASSERT__
        int res =
#endif
            PyDict_SetItemString( module_dict, "__builtins__", PyEval_GetBuiltins() );

        assert( res == 0 );
    }

    // Module code
    bool traceback = false;

    try
    {
        // To restore the initial exception, could be made dependent on actual try/except statement
        // as it is done for functions/classes already.
        FrameExceptionKeeper _frame_exception_keeper;
%(module_code)s
    }
    catch ( _PythonException &_exception )
    {
        if ( traceback == false )
        {
            _exception.addTraceback( frameobj_%(module_identifier)s() );
        }

        _exception.toPython();
    }

    // puts( "out init%(module_identifier)s" );
}
"""

module_init_no_package_template = """\
    _mvar_%(module_identifier)s___doc__.assign0( %(doc_identifier)s );
    _mvar_%(module_identifier)s___file__.assign0( %(filename_identifier)s );
#if %(is_package)d
    _mvar_%(module_identifier)s___path__.assign0( %(path_identifier)s );
#endif

#ifdef _NUITKA_MODULE
    // Set the package attribute from what the import mechanism provided. The package
    // variable should be set for the module code already.
    if ( qualified_name )
    {
        _mvar_%(module_identifier)s___package__.assign0(
            PyString_FromStringAndSize(
               qualified_name,
               strrchr( qualified_name, '.' ) -  qualified_name
            )
        );
    }
#endif"""

module_init_in_package_template = """\
    _mvar_%(module_identifier)s___doc__.assign0( %(doc_identifier)s );
    _mvar_%(module_identifier)s___file__.assign0( %(filename_identifier)s );
#if %(is_package)d
    _mvar_%(module_identifier)s___path__.assign0( %(path_identifier)s );
#endif
    _mvar_%(module_identifier)s___package__.assign0( %(package_name_identifier)s );

    // The package must already be imported.
    assertObject( _module_%(package_identifier)s );

    SET_ATTRIBUTE(
        _module_%(package_identifier)s,
        %(module_name)s,
        _module_%(module_identifier)s
    );
"""

template_header_guard = """\
#ifndef %(header_guard_name)s
#define %(header_guard_name)s

%(header_body)s
#endif
"""
