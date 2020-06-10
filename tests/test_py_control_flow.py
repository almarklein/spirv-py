"""
Tests that run a compute shader and validate the outcome.
With this we can validate arithmetic, control flow etc.
"""


import ctypes

import python_shader

from python_shader import f32, i32, vec2, vec3, vec4, Array  # noqa

import wgpu.backends.rs  # noqa
from wgpu.utils import compute_with_buffers

import pytest
from testutils import can_use_wgpu_lib
from testutils import validate_module, run_test_and_print_new_hashes


def generate_list_of_floats_from_shader(n, compute_shader):
    inp_arrays = {}
    out_arrays = {1: ctypes.c_float * n}
    out = compute_with_buffers(inp_arrays, out_arrays, compute_shader)
    return list(out[1])


# %% if


def test_if1():
    # Simple
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        if index < 2:
            data2[index] = 40.0
        elif index < 4:
            data2[index] = 41.0
        elif index < 8:
            data2[index] = 42.0
        else:
            data2[index] = 43.0

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [40, 40, 41, 41, 42, 42, 42, 42, 43, 43]


def test_if2():
    # More nesting
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        if index < 2:
            if index == 0:
                data2[index] = 40.0
            else:
                data2[index] = 41.0
        elif index < 4:
            data2[index] = 42.0
            if index > 2:
                data2[index] = 43.0
        elif index < 8:
            data2[index] = 45.0
            if index <= 6:
                if index <= 5:
                    if index == 4:
                        data2[index] = 44.0
                    elif index == 5:
                        data2[index] = 45.0
                elif index == 6:
                    data2[index] = 46.0
            else:
                data2[index] = 47.0
        else:
            if index == 9:
                data2[index] = 49.0
            else:
                data2[index] = 48.0

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [40, 41, 42, 43, 44, 45, 46, 47, 48, 49]


def test_if3():
    # And and or
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        if index < 2 or index > 7 or index == 4:
            data2[index] = 40.0
        elif index > 3 and index < 6:
            data2[index] = 41.0
        else:
            data2[index] = 43.0

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [40, 40, 43, 43, 40, 41, 43, 43, 40, 40]


def test_if4():
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32),
        data1: ("buffer", 0, Array(f32)),
        data2: ("buffer", 1, Array(f32)),
    ):
        a = f32(index)
        if index < 2:
            a = 100.0
        elif index < 8:
            a = a + 10.0
            if index < 6:
                a = a + 1.0
            else:
                a = a + 2.0
        else:
            a = 200.0
            if index < 9:
                a = a + 1.0
        data2[index] = a

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [100, 100, 2 + 11, 3 + 11, 4 + 11, 5 + 11, 6 + 12, 7 + 12, 201, 200]


def test_if5():
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        x = False
        if index < 2:
            data2[index] = 40.0
        elif index < 4:
            data2[index] = 41.0
        elif index < 8:
            x = True
        else:
            data2[index] = 43.0
        if x:
            data2[index] = 42.0

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [40, 40, 41, 41, 42, 42, 42, 42, 43, 43]


# %% ternary


def test_ternary1():
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        data2[index] = 40.0 if index == 0 else 41.0

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [40, 41, 41, 41, 41, 41, 41, 41, 41, 41]


def test_ternary2():
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        data2[index] = (
            40.0
            if index == 0
            else ((41.0 if index == 1 else 42.0) if index < 3 else 43.0)
        )

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [40, 41, 42, 43, 43, 43, 43, 43, 43, 43]


def test_ternary3():
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        data2[index] = (
            (10.0 * 4.0)
            if index == 0
            else ((39.0 + 2.0) if index == 1 else (50.0 - 8.0))
        )

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [40, 41, 42, 42, 42, 42, 42, 42, 42, 42]


def test_ternary_cf1():
    python_shader.py.OPT_CONVERT_TERNARY_TO_SELECT = False
    try:

        @python2shader_and_validate
        def compute_shader(
            index: ("input", "GlobalInvocationId", i32),
            data2: ("buffer", 1, Array(f32)),
        ):
            data2[index] = 40.0 if index == 0 else 41.0

    finally:
        python_shader.py.OPT_CONVERT_TERNARY_TO_SELECT = True

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [40, 41, 41, 41, 41, 41, 41, 41, 41, 41]


def test_ternary_cf2():
    python_shader.py.OPT_CONVERT_TERNARY_TO_SELECT = False
    try:

        @python2shader_and_validate
        def compute_shader(
            index: ("input", "GlobalInvocationId", i32),
            data2: ("buffer", 1, Array(f32)),
        ):
            data2[index] = (
                40.0
                if index == 0
                else ((41.0 if index == 1 else 42.0) if index < 3 else 43.0)
            )

    finally:
        python_shader.py.OPT_CONVERT_TERNARY_TO_SELECT = True

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [40, 41, 42, 43, 43, 43, 43, 43, 43, 43]


def test_ternary_cf3():
    python_shader.py.OPT_CONVERT_TERNARY_TO_SELECT = False
    try:

        @python2shader_and_validate
        def compute_shader(
            index: ("input", "GlobalInvocationId", i32),
            data2: ("buffer", 1, Array(f32)),
        ):
            data2[index] = (
                (10.0 * 4.0)
                if index == 0
                else ((39.0 + 2.0) if index == 1 else (50.0 - 8.0))
            )

    finally:
        python_shader.py.OPT_CONVERT_TERNARY_TO_SELECT = True

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [40, 41, 42, 42, 42, 42, 42, 42, 42, 42]


# %% more or / and


def test_andor1():
    # Implicit conversion to truth values is not supported

    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        if index < 5:
            val = f32(index - 3) and 99.0
        else:
            val = f32(index - 6) and 99.0
        data2[index] = val

    with pytest.raises(python_shader.ShaderError):
        python_shader.python2shader(compute_shader)


def test_andor2():
    # or a lot
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        if index == 2 or index == 3 or index == 5:
            data2[index] = 40.0
        elif index == 2 or index == 6 or index == 7:
            data2[index] = 41.0
        else:
            data2[index] = 43.0

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [43, 43, 40, 40, 43, 40, 41, 41, 43, 43]


def test_andor3():
    # and a lot
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        mod = index % 2
        if index < 4 and mod == 0:
            data2[index] = 2.0
        elif index > 5 and mod == 1:
            data2[index] = 3.0
        else:
            data2[index] = 1.0

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [2, 1, 2, 1, 1, 1, 1, 3, 1, 3]


def test_andor4():
    # mix it up
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        mod = index % 2
        if index < 4 and mod == 0 or index == 5:
            data2[index] = 2.0
        elif index > 5 and mod == 1 or index == 4:
            data2[index] = 3.0
        else:
            data2[index] = 1.0

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [2, 1, 2, 1, 3, 2, 1, 3, 1, 3]


def test_andor5():
    # in a ternary
    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        mod = index % 2
        data2[index] = 40.0 if (index == 1 or index == 3) else 41.0
        # if index < 5:
        # else:
        # data2[index] = 42.0 if (index > 7 and mod == 1) else 43.0

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [40, 41, 41, 41, 41, 41, 41, 41, 41, 41]


# %% loops


def test_loop1():
    # Simplest form

    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        val = 0.0
        for i in range(index):
            val = val + 1.0
        data2[index] = val

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


def test_loop2():
    # With a ternary in the body

    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        val = 0.0
        for i in range(index):
            val = val + (1.0 if i < 5 else 2.0)

        data2[index] = val

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [0, 1, 2, 3, 4, 5, 7, 9, 11, 13]


def test_loop3():
    # With an if in the body

    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        val = 0.0
        for i in range(index):
            if i < 5:
                val = val + 1.0
            else:
                val = val + 2.0
        data2[index] = val

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [0, 1, 2, 3, 4, 5, 7, 9, 11, 13]


def test_loop4():
    # A loop in a loop

    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        val = 0.0
        for i in range(index):
            for j in range(3):
                val = val + 10.0
                for k in range(2):
                    val = val + 2.0
            for k in range(10):
                val = val - 1.0
        data2[index] = val

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [0, 32, 64, 96, 128, 160, 192, 224, 256, 288]


def test_loop5():
    # Break - this one is interesting because the stop criterion is combined with the break
    # This is a consequence of the logic to detect and simplify or-logic

    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        val = 0.0
        for i in range(index):
            if i == 7:
                break
            val = val + 1.0
        data2[index] = val

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [0, 1, 2, 3, 4, 5, 6, 7, 7, 7]


def test_loop6():
    # Test both continue and break

    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        val = 0.0
        for i in range(index):
            if index == 4:
                continue
            elif i == 7:
                break
            val = val + 1.0
        data2[index] = val

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [0, 1, 2, 3, 0, 5, 6, 7, 7, 7]


def test_loop7():
    # Use start and stop

    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        val = 0.0
        for i in range(3, index):
            val = val + 1.0
        data2[index] = val

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [0, 0, 0, 0, 1, 2, 3, 4, 5, 6]


def test_loop8():
    # Use start and stop and step

    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        val = 0.0
        for i in range(3, index, 2):
            val = val + 1.0
        data2[index] = val

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [0, 0, 0, 0, 1, 1, 2, 2, 3, 3]


def test_while1():
    # A simple while loop!

    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        val = 0.0
        while val < f32(index):
            val = val + 2.0
        data2[index] = val

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [0, 2, 2, 4, 4, 6, 6, 8, 8, 10]


def test_while2():
    # Test while with continue and break

    @python2shader_and_validate
    def compute_shader(
        index: ("input", "GlobalInvocationId", i32), data2: ("buffer", 1, Array(f32)),
    ):
        val = 0.0
        i = 0
        while i < index:
            if index == 4:
                continue
            elif i == 7:
                break
            val = val + 1.0
            i = i + 1
        data2[index] = val

    skip_if_no_wgpu()
    res = generate_list_of_floats_from_shader(10, compute_shader)
    assert res == [0, 1, 2, 3, 0, 5, 6, 7, 7, 7]


# %% discard


def test_discard():

    # A fragment shader for drawing red dots
    @python2shader_and_validate
    def fragment_shader(in_coord: ("input", "PointCoord", vec2),):
        r2 = ((in_coord.x - 0.5) * 2.0) ** 2 + ((in_coord.y - 0.5) * 2.0) ** 2
        if r2 > 1.0:
            return  # discard
        out_color = vec4(1.0, 0.0, 0.0, 1.0)  # noqa - shader output

    assert ("co_return",) in fragment_shader.to_bytecode()
    assert "OpKill" in fragment_shader.gen.to_text()


# %% Utils for this module


def python2shader_and_validate(func):
    m = python_shader.python2shader(func)
    assert m.input is func
    validate_module(m, HASHES)
    return m


def skip_if_no_wgpu():
    if not can_use_wgpu_lib:
        raise pytest.skip(msg="SpirV validated, but not run (cannot use wgpu)")


HASHES = {
    "test_if1.compute_shader": ("425becc765f1b063", "df47945efe25f3e0"),
    "test_if2.compute_shader": ("2fcd2b0ffdd74b00", "f931b5238c6a8593"),
    "test_if3.compute_shader": ("eed2242bc723bc19", "5fd34c5a756c0128"),
    "test_if4.compute_shader": ("9dcf1f3cfaff479d", "7f101ed4facfe1fd"),
    "test_if5.compute_shader": ("35d6f557a5a3a23f", "0bd1a694b5cd4656"),
    "test_ternary1.compute_shader": ("78a6f5034f5d9c25", "316086560fab4faf"),
    "test_ternary2.compute_shader": ("876484851fd42095", "5d3cce752b4d7535"),
    "test_ternary3.compute_shader": ("6e70f44cd9129c93", "4152284068243d3b"),
    "test_ternary_cf1.compute_shader": ("5ddfcb0497e4e918", "6055b9b66cef6a45"),
    "test_ternary_cf2.compute_shader": ("d071ee52ed031ae0", "0fc5a0f41eee5f0d"),
    "test_ternary_cf3.compute_shader": ("713a15d1315973ee", "791e0c70f0fbbf92"),
    "test_loop1.compute_shader": ("e6b2fbb992a727f4", "8c9c9af924e92f14"),
    "test_loop2.compute_shader": ("e5b15e86683c234b", "f23caa3999cec193"),
    "test_loop3.compute_shader": ("6daf801ca352d8bf", "57b06ed205152275"),
    "test_loop4.compute_shader": ("d0a6263225e1c5e9", "52fdcb999ecdfab0"),
    "test_loop5.compute_shader": ("7dcf26dbdad5d2c2", "b766a0d1362fa9c2"),
    "test_loop6.compute_shader": ("0214ce5d9493dcb4", "3e1d5e4038cbedc7"),
    "test_loop7.compute_shader": ("875d18a952bdc11a", "bd741df0657431a7"),
    "test_loop8.compute_shader": ("a864ceb208046ec4", "347b7c89df6fd5ac"),
    "test_while1.compute_shader": ("32a93264e56c9deb", "bbda0ee55cc3b891"),
    "test_while2.compute_shader": ("d77a0278a61d0140", "5dd17ee5889df55e"),
    "test_discard.fragment_shader": ("8d73bfc370da9504", "6d3182b0b5189d45"),
}


if __name__ == "__main__":
    run_test_and_print_new_hashes(globals())
