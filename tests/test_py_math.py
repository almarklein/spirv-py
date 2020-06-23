"""
Tests that run a compute shader and validate the outcome.
With this we can validate arithmetic, control flow etc.
"""

import os
import math
import json
import random
import ctypes

import pyshader

from pyshader import f32, i32, vec2, vec3, vec4, Array  # noqa

import wgpu.backends.rs  # noqa
from wgpu.utils import compute_with_buffers

import pytest
from testutils import can_use_wgpu_lib, iters_close
from testutils import validate_module, run_test_and_print_new_hashes


THIS_DIR = os.path.dirname(os.path.abspath(__file__))


# %% Builtin math


def test_add_sub1():
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32),
        data1: ("buffer", 0, Array(f32)),
        data2: ("buffer", 1, Array(vec2)),
    ):
        a = data1[index]
        data2[index] = vec2(a + 1.0, a - 1.0)

    skip_if_no_wgpu()

    values1 = [i - 5 for i in range(10)]

    inp_arrays = {0: (ctypes.c_float * 10)(*values1)}
    out_arrays = {1: ctypes.c_float * 20}
    out = compute_with_buffers(inp_arrays, out_arrays, compute_shader)

    res = list(out[1])
    assert res[0::2] == [i + 1 for i in values1]
    assert res[1::2] == [i - 1 for i in values1]


def test_add_sub2():
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32),
        data1: ("buffer", 0, Array(f32)),
        data2: ("buffer", 1, Array(vec2)),
    ):
        a = data1[index]
        data2[index] = vec2(a + 1.0, a - 1.0) + 20.0

    skip_if_no_wgpu()

    values1 = [i - 5 for i in range(10)]

    inp_arrays = {0: (ctypes.c_float * 10)(*values1)}
    out_arrays = {1: ctypes.c_float * 20}
    out = compute_with_buffers(inp_arrays, out_arrays, compute_shader)

    res = list(out[1])
    assert res[0::2] == [20.0 + i + 1 for i in values1]
    assert res[1::2] == [20.0 + i - 1 for i in values1]


def test_add_sub3():
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32),
        data1: ("buffer", 0, Array(f32)),
        data2: ("buffer", 1, Array(vec2)),
    ):
        a = data1[index]
        a -= -1.0
        b = vec2(a, a)
        b += 2.0
        data2[index] = b

    skip_if_no_wgpu()

    values1 = [i - 5 for i in range(10)]

    inp_arrays = {0: (ctypes.c_float * 10)(*values1)}
    out_arrays = {1: ctypes.c_float * 20}
    out = compute_with_buffers(inp_arrays, out_arrays, compute_shader)

    res = list(out[1])
    assert res[0::2] == [i + 3 for i in values1]
    assert res[1::2] == [i + 3 for i in values1]


def test_mul_div1():
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32),
        data1: ("buffer", 0, Array(f32)),
        data2: ("buffer", 1, Array(vec2)),
    ):
        a = data1[index]
        data2[index] = vec2(a * 2.0, a / 2.0)

    skip_if_no_wgpu()

    values1 = [i - 5 for i in range(10)]

    inp_arrays = {0: (ctypes.c_float * 10)(*values1)}
    out_arrays = {1: ctypes.c_float * 20}
    out = compute_with_buffers(inp_arrays, out_arrays, compute_shader)

    res = list(out[1])
    assert res[0::2] == [i * 2 for i in values1]
    assert res[1::2] == [i / 2 for i in values1]


def test_mul_div2():
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32),
        data1: ("buffer", 0, Array(f32)),
        data2: ("buffer", 1, Array(vec2)),
    ):
        a = data1[index]
        data2[index] = 2.0 * vec2(a * 2.0, a / 2.0) * 3.0

    skip_if_no_wgpu()

    values1 = [i - 5 for i in range(10)]

    inp_arrays = {0: (ctypes.c_float * 10)(*values1)}
    out_arrays = {1: ctypes.c_float * 20}
    out = compute_with_buffers(inp_arrays, out_arrays, compute_shader)

    res = list(out[1])
    assert res[0::2] == [6 * i * 2 for i in values1]
    assert res[1::2] == [6 * i / 2 for i in values1]


def test_mul_div3():
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32),
        data1: ("buffer", 0, Array(f32)),
        data2: ("buffer", 1, Array(vec2)),
    ):
        a = data1[index]
        a /= -1.0
        b = vec2(a, a)
        b *= 2.0
        data2[index] = b

    skip_if_no_wgpu()

    values1 = [i - 5 for i in range(10)]

    inp_arrays = {0: (ctypes.c_float * 10)(*values1)}
    out_arrays = {1: ctypes.c_float * 20}
    out = compute_with_buffers(inp_arrays, out_arrays, compute_shader)

    res = list(out[1])
    assert res[0::2] == [-i * 2 for i in values1]
    assert res[1::2] == [-i * 2 for i in values1]


def test_integer_div():
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32),
        data1: ("buffer", 0, Array(i32)),
        data2: ("buffer", 1, Array(i32)),
    ):
        a = data1[index]
        data2[index] = 12 // a

    skip_if_no_wgpu()

    values1 = [(i - 5) or 12 for i in range(10)]

    inp_arrays = {0: (ctypes.c_int * 10)(*values1)}
    out_arrays = {1: ctypes.c_int * 10}
    out = compute_with_buffers(inp_arrays, out_arrays, compute_shader)

    # NOTE: the shader // truncates, not floor like Python
    res = list(out[1])
    assert res == [math.trunc(12 / i) for i in values1]


def test_mul_modulo():
    # There are two module functions, one in which the result takes the sign
    # of the divisor and one in which it takes the sign of the divident.
    # In Python these are `%` and math.fmod respectively. Here we test that
    # the SpirV code matches that (fmod and frem).
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32),
        data1: ("buffer", 0, Array(vec2)),
        data2: ("buffer", 1, Array(vec2)),
    ):
        a = data1[index]
        data2[index] = vec2(a.x % a.y, math.fmod(a.x, a.y))

    skip_if_no_wgpu()

    values1 = [i - 5 for i in range(10)]
    values2 = [-2 if i % 2 else 2 for i in range(10)]
    values = sum(zip(values1, values2), ())

    inp_arrays = {0: (ctypes.c_float * 20)(*values)}
    out_arrays = {1: ctypes.c_float * 20}
    out = compute_with_buffers(inp_arrays, out_arrays, compute_shader)

    res = list(out[1])
    assert res[0::2] == [i % j for i, j in zip(values1, values2)]
    assert res[1::2] == [math.fmod(i, j) for i, j in zip(values1, values2)]


def test_math_constants():
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        if index % 2 == 0:
            data2[index] = math.pi
        else:
            data2[index] = math.e

    skip_if_no_wgpu()

    out = compute_with_buffers({}, {1: ctypes.c_float * 10}, compute_shader, n=10)

    res = list(out[1])
    assert iters_close(res, [math.pi, math.e] * 5)


# %% Extension functions

# We test a subset; we test the definition of all functions in test_ext_func_definitions


def test_pow():
    # note hat a**2 is converted to a*a and a**0.5 to sqrt(a)
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32),
        data1: ("buffer", 0, Array(f32)),
        data2: ("buffer", 1, Array(vec4)),
    ):
        a = data1[index]
        data2[index] = vec4(a ** 2, a ** 0.5, a ** 3.0, a ** 3.1)

    skip_if_no_wgpu()

    values1 = [i - 5 for i in range(10)]

    inp_arrays = {0: (ctypes.c_float * 10)(*values1)}
    out_arrays = {1: ctypes.c_float * 40}
    out = compute_with_buffers(inp_arrays, out_arrays, compute_shader)

    res = list(out[1])
    assert res[0::4] == [i ** 2 for i in values1]
    assert iters_close(res[1::4], [i ** 0.5 for i in values1])
    assert res[2::4] == [i ** 3 for i in values1]
    assert iters_close(res[3::4], [i ** 3.1 for i in values1])


def test_sqrt():
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32),
        data1: ("buffer", 0, Array(f32)),
        data2: ("buffer", 1, Array(vec3)),
    ):
        a = data1[index]
        data2[index] = vec3(a ** 0.5, math.sqrt(a), stdlib.sqrt(a))

    skip_if_no_wgpu()

    values1 = [i for i in range(10)]

    inp_arrays = {0: (ctypes.c_float * 10)(*values1)}
    out_arrays = {1: ctypes.c_float * 30}
    out = compute_with_buffers(inp_arrays, out_arrays, compute_shader)

    res = list(out[1])
    ref = [i ** 0.5 for i in values1]
    assert iters_close(res[0::3], ref)
    assert iters_close(res[1::3], ref)
    assert iters_close(res[2::3], ref)


def test_length():
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32),
        data1: ("buffer", 0, Array(vec2)),
        data2: ("buffer", 1, Array(f32)),
    ):
        data2[index] = length(data1[index])

    skip_if_no_wgpu()

    values1 = [random.uniform(-2, 2) for i in range(20)]

    inp_arrays = {0: (ctypes.c_float * 20)(*values1)}
    out_arrays = {1: ctypes.c_float * 10}
    out = compute_with_buffers(inp_arrays, out_arrays, compute_shader, n=10)

    res = list(out[1])
    ref = [(values1[i * 2] ** 2 + values1[i * 2 + 1] ** 2) ** 0.5 for i in range(10)]
    assert iters_close(res, ref)


def test_normalize():
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32),
        data1: ("buffer", 0, Array(f32)),
        data2: ("buffer", 1, Array(vec2)),
    ):
        v = data1[index]
        data2[index] = normalize(vec2(v, v))

    skip_if_no_wgpu()

    values1 = [i - 5 for i in range(10)]

    inp_arrays = {0: (ctypes.c_float * 10)(*values1)}
    out_arrays = {1: ctypes.c_float * 20}
    out = compute_with_buffers(inp_arrays, out_arrays, compute_shader, n=10)

    res = list(out[1])
    ref = []
    assert iters_close(res[:10], [-2**0.5/2 for i in range(10)])
    assert iters_close(res[-8:], [+2**0.5/2 for i in range(8)])
    assert math.isnan(res[10]) and math.isnan(res[11])  # or can this also be inf?


# %% Extension functions that need more care

# Mostly because they operate on more types than just float and vec.
# We'll want to test all "hardcoded" functions here.


def test_abs():
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32),
        data1: ("buffer", 0, Array(f32)),
        data2: ("buffer", 1, Array(i32)),
        data3: ("buffer", 2, Array(vec2)),
    ):
        v1 = abs(data1[index])  # float
        v2 = abs(data2[index])  # int
        data3[index] = vec2(f32(v1), v2)

    skip_if_no_wgpu()

    values1 = [random.uniform(-2, 2) for i in range(10)]
    values2 = [random.randint(-100, 100) for i in range(10)]

    inp_arrays = {0: (ctypes.c_float * 10)(*values1), 1: (ctypes.c_int * 10)(*values2)}
    out_arrays = {2: ctypes.c_float * 20}
    out = compute_with_buffers(inp_arrays, out_arrays, compute_shader, n=10)

    res = list(out[2])
    assert iters_close(res[0::2], [abs(v) for v in values1])
    assert res[1::2] == [abs(v) for v in values2]


def test_min_max_clamp():
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32),
        data1: ("buffer", 0, Array(vec3)),
        data2: ("buffer", 1, Array(vec3)),
        data3: ("buffer", 2, Array(vec3)),
    ):
        v = data1[index].x
        mi = data1[index].y
        ma = data1[index].z

        data2[index] = vec3(min(v, ma), max(v, mi), clamp(v, mi, ma))
        data3[index] = vec3(nmin(v, ma), nmax(v, mi), nclamp(v, mi, ma))

    skip_if_no_wgpu()

    the_vals = [-4, -3, -2, -1, +0, +0, +1, +2, +3, +4]
    min_vals = [-2, -5, -5, +2, +2, -1, +3, +1, +1, -6]
    max_vals = [+2, -1, -3, +3, +3, +1, +9, +9, +2, -3]
    values = sum(zip(the_vals, min_vals, max_vals), ())

    inp_arrays = {0: (ctypes.c_float * 30)(*values)}
    out_arrays = {1: ctypes.c_float * 30, 2: ctypes.c_float * 30}
    out = compute_with_buffers(inp_arrays, out_arrays, compute_shader, n=10)

    res1 = list(out[1])
    res2 = list(out[2])
    ref_min = [min(the_vals[i], max_vals[i]) for i in range(10)]
    ref_max = [max(the_vals[i], min_vals[i]) for i in range(10)]
    ref_clamp = [min(max(min_vals[i], the_vals[i]), max_vals[i]) for i in range(10)]
    # Test normal variant
    assert res1[0::3] == ref_min
    assert res1[1::3] == ref_max
    assert res1[2::3] == ref_clamp
    # Test NaN-safe variant
    assert res2[0::3] == ref_min
    assert res2[1::3] == ref_max
    assert res2[2::3] == ref_clamp


def test_mix():
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32),
        data1: ("buffer", 0, Array(vec3)),
        data2: ("buffer", 1, Array(vec3)),
    ):
        v = data1[index]
        v1 = mix(v.x, v.y, v.z)
        v2 = mix(vec2(v.x, v.x), vec2(v.y, v.y), v.z)
        data2[index] = vec3(v1, v2.x, v2.y)

    skip_if_no_wgpu()

    values1 = [-4, -3, -2, -1, +0, +0, +1, +2, +3, +4]
    values2 = [-2, -5, -5, +2, +2, -1, +3, +1, +1, -6]
    weights = [0.1 * i for i in range(10)]
    values = sum(zip(values1, values2, weights), ())

    inp_arrays = {0: (ctypes.c_float * 30)(*values)}
    out_arrays = {1: ctypes.c_float * 30}
    out = compute_with_buffers(inp_arrays, out_arrays, compute_shader, n=10)

    res = list(out[1])
    ref = [values1[i] * (1 - w) + values2[i] * w for i, w in enumerate(weights)]
    assert iters_close(res[0::3], ref)
    assert iters_close(res[1::3], ref)
    assert iters_close(res[2::3], ref)


# %% Extension function definitions


def test_ext_func_definitions():
    # The above tests touch a subset of all extension functions.
    # This test validates that the extension functions that we define
    # in stdlib.py have the correct enum nr and number of arguments.

    # Prepare meta data about instructions
    instructions = {}
    with open(os.path.join(THIS_DIR, "extinst.glsl.std.450.grammar.json"), "r") as f:
        meta = json.load(f)
    for x in meta["instructions"]:
        normalized_name = x["opname"].lower()
        instructions[normalized_name] = x["opcode"], len(x["operands"])

    # Check each function
    count = 0
    for name, info in pyshader.stdlib.ext_functions.items():
        if not info:
            continue  # skip the hardcoded functions
        normalized_name = name.replace("_", "")
        if normalized_name not in instructions:
            normalized_name = "f" + normalized_name
        assert normalized_name in instructions, f"Could not find meta data for {name}()"
        nr, nargs = instructions[normalized_name]
        assert (
            info["nr"] == nr
        ), f"Invalid enum nr for {name}: {info['nr']} instead of {nr}"
        assert (
            info["nargs"] == nargs
        ), f"Invalud nargs for {name}: {info['nargs']} instead of {nargs}"
        count += 1

    print(f"Validated {count} extension functions!")


# %% Utils for this module


def python2shader_and_validate(func):
    m = pyshader.python2shader(func)
    assert m.input is func
    validate_module(m, HASHES)
    return m


def skip_if_no_wgpu():
    if not can_use_wgpu_lib:
        raise pytest.skip(msg="SpirV validated, but not run (cannot use wgpu)")


HASHES = {
    "test_add_sub1.compute_shader": ("f5f5e1f5d546615f", "2edf296df860a93d"),
    "test_add_sub2.compute_shader": ("eac80cea3cae0305", "785f2c0acdbe0cd3"),
    "test_add_sub3.compute_shader": ("ff8f23434e6d6879", "26a092691cff2104"),
    "test_mul_div1.compute_shader": ("15609b10642943d4", "3b804bb4b7b52de0"),
    "test_mul_div2.compute_shader": ("f4c102543e3f0339", "7e9591cb2d93d067"),
    "test_mul_div3.compute_shader": ("3aec875ee04bc331", "d6fa9c27744f4f8b"),
    "test_integer_div.compute_shader": ("3e957da5a67c96a8", "c1e635c9800b2975"),
    "test_mul_modulo.compute_shader": ("28c42b8b719b94cf", "cd29c63a99af0a7c"),
    "test_math_constants.compute_shader": ("425b33e1d60a6105", "ab0b82f58688bbc7"),
    "test_pow.compute_shader": ("c83ff35156e57f86", "4c41b41333f94ee9"),
    "test_sqrt.compute_shader": ("3fb9f30103054be5", "a18522c9c8bbf809"),
    "test_length.compute_shader": ("bcb9fb5793f33610", "2e0a4f0ac0f3468d"),
    "test_normalize.compute_shader": ("644816afceb0ec7f", "b296aa6a0f80445c"),
    "test_abs.compute_shader": ("09922efbd3b835a9", "48c14af6ab79385f"),
    "test_min_max_clamp.compute_shader": ("d0b7f20a0c81aea0", "8f3b43edd3f5e049"),
    "test_mix.compute_shader": ("21e44597b4cb97f3", "5157f868b2495a4d"),
}


if __name__ == "__main__":
    run_test_and_print_new_hashes(globals())
