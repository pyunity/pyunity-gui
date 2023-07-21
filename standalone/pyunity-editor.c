#define PY_SSIZE_T_CLEAN
#define Py_LIMITED_API 0x03060000
#include <Python.h>

#ifdef NOCONSOLE
#include <windows.h>
#define CHECK_ERROR() if (PyErr_Occurred() != NULL) { showError(); exit(1); }

void showError() {
    printf("Error encountered\n");
    SetEnvironmentVariable("PYUNITY_EDITOR_LOADED", "1");
    PyObject *type, *value, *traceback;
    PyErr_Fetch(&type, &value, &traceback);
    PyErr_Print();

    PyObject *tracebackModule = PyImport_ImportModule("traceback");
    PyObject *formatFunc = PyObject_GetAttrString(tracebackModule, "format_exception");
    Py_DecRef(tracebackModule);

    PyErr_NormalizeException(&type, &value, &traceback);
    PyException_SetTraceback(value, traceback);

    PyObject *lines = PyObject_CallFunctionObjArgs(formatFunc, value, NULL);
    PyObject *sep = PyUnicode_FromString("");
    PyObject *joined = PyUnicode_Join(sep, lines);
    Py_DecRef(sep);
    Py_DecRef(lines);

    wchar_t *msg = PyUnicode_AsWideCharString(joined, NULL);
    MessageBoxW(NULL, msg, L"Error loading PyUnity Editor", 0x10L);
    PyMem_Free(msg);

    PyErr_Restore(type, value, traceback);
}
#else
#define CHECK_ERROR() if (PyErr_Occurred() != NULL) { PyErr_Print(); exit(1); }
#endif

int main(int argc, char **argv) {
    wchar_t *path = Py_DecodeLocale("Lib\\python.zip;Lib\\;Lib\\win32", NULL);
    Py_SetPath(path);

    wchar_t **program = (wchar_t**)PyMem_Malloc(sizeof(wchar_t**) * argc);
    for (int i = 0; i < argc; i++) {
        program[i] = Py_DecodeLocale(argv[i], NULL);
    }
    if (program[0] == NULL) {
        #ifdef NOCONSOLE
        MessageBoxW(NULL, L"Fatal error: cannot decode argv[0]", L"Error loading PyUnity Editor", 0x10L);
        #else
        fprintf(stderr, "Fatal error: cannot decode argv[0]\n");
        #endif
        exit(1);
    }
    Py_SetProgramName(program[0]);
    Py_Initialize();
    PySys_SetArgvEx(argc, program, 0);
    CHECK_ERROR();

    PyObject *left = Py_BuildValue("u", program[1]);
    PyObject *right1 = Py_BuildValue("s", "-i");
    PyObject *right2 = Py_BuildValue("s", "--interactive");
    if (PyUnicode_Compare(left, right1) == 0 ||
            PyUnicode_Compare(left, right2) == 0) {
        #ifdef NOCONSOLE
        if (AllocConsole() == 0) {
            MessageBoxW(NULL, L"Cannot allocate console", L"Error loading PyUnity Editor", 0x10L);
            exit(1);
        }
        #endif
        program[1] = Py_DecodeLocale("-E", NULL);
        int retcode = Py_Main(argc, program);
        exit(retcode);
    }
    PyObject *right3 = Py_BuildValue("s", "-U");
    PyObject *right4 = Py_BuildValue("s", "--update");
    if (PyUnicode_Compare(left, right3) == 0 ||
            PyUnicode_Compare(left, right4) == 0) {
        PyObject *updater = PyImport_ImportModule("pyunity_updater");
        CHECK_ERROR();
        PyObject *func = PyObject_GetAttrString(updater, "main");
        CHECK_ERROR();
        PyObject_CallFunction(func, NULL);
        CHECK_ERROR();
    } else {
        PyObject *editor = PyImport_ImportModule("pyunity_editor.cli");
        CHECK_ERROR();

        #ifdef NOCONSOLE
        PyObject *func = PyObject_GetAttrString(editor, "gui");
        #else
        PyObject *func = PyObject_GetAttrString(editor, "run");
        #endif
        CHECK_ERROR();

        PyObject_CallFunction(func, NULL);
        CHECK_ERROR();
    }

    if (Py_FinalizeEx() < 0) {
        exit(1);
    }
    for (int i = 0; i < argc; i++) {
        PyMem_Free((void*)program[i]);
    }
    PyMem_Free((void*)program);
    PyMem_Free((void*)path);
    printf("Safely freed memory\n");
    return 0;
}

#ifdef NOCONSOLE
int __stdcall WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance,
        char* pCmdLine, int nShowCmd) {
    return main(__argc, __argv);
}
#endif
