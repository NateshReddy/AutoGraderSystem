test_cases = {
    "Sum2.pdf": [
        {"input": (1, 2), "expected_output": 3},
        {"input": (10, 20), "expected_output": 30},
        {"input": (-5, 5), "expected_output": 0},
        {"input": (100, 200), "expected_output": 300},
        {"input": (-10, -20), "expected_output": -30},
        {"input": (123, 456), "expected_output": 579},
        {"input": (0, 0), "expected_output": 0},
        {"input": (999, 1), "expected_output": 1000},
    ],
    "KnightAttack.pdf": [
        {"input": (8, 1, 1, 2, 2), "expected_output": 2},
        {"input": (8, 1, 1, 2, 3), "expected_output": 1},
        {"input": (8, 0, 3, 4, 2), "expected_output": 3},
        {"input": (8, 0, 3, 5, 2), "expected_output": 4},
        {"input": (24, 4, 7, 19, 20), "expected_output": 10},
        {"input": (100, 21, 10, 0, 0), "expected_output": 11},
        {"input": (3, 0, 0, 1, 2), "expected_output": 1},
        {"input": (3, 0, 0, 1, 1), "expected_output": None},
    ]
}

def get_test_cases(pdf_name):
    return test_cases.get(pdf_name, [])
