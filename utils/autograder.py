import os
import importlib.util
import time
from decimal import Decimal
from utils.test_cases import get_test_cases
import threading

class AutoGrader:
    def __init__(self, pdf_name, solution_file):
        self.pdf_name = pdf_name
        self.solution_file = solution_file
        self.test_cases = get_test_cases(pdf_name)
        self.function_name = self.get_function_name()
        self.timeout = 2  # Set the timeout limit for each test case in seconds

    def get_function_name(self):
        # Map PDF names to function names
        function_map = {
            "Sum2.pdf": "add",
            "KnightAttack.pdf": "knight_attack",
            # Add more mappings as needed
        }
        return function_map.get(self.pdf_name, None)

    def load_solution(self):
        module_name = os.path.splitext(os.path.basename(self.solution_file))[0]
        spec = importlib.util.spec_from_file_location(module_name, self.solution_file)
        solution = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(solution)
        return solution

    def run_with_timeout(self, func, args, timeout):
        result = [None]
        exception = [None]
        
        def target():
            try:
                result[0] = func(*args)
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            return None, "Timeout"
        if exception[0] is not None:
            raise exception[0]
        return result[0], None

    def grade(self):
        results = []
        passed_tests = 0
        total_tests = len(self.test_cases)

        try:
            solution = self.load_solution()
            function_name = self.function_name
            if not function_name or not hasattr(solution, function_name):
                raise ValueError(f"Function {function_name} not found in solution file.")
            
            function_to_test = getattr(solution, function_name)

            for idx, test in enumerate(self.test_cases):
                input_args = test["input"]
                expected_output = test["expected_output"]
                start_time = time.time()
                try:
                    result, error = self.run_with_timeout(function_to_test, input_args, self.timeout)
                    end_time = time.time()
                    execution_time = (end_time - start_time) * 1000  # in milliseconds
                    
                    if error == "Timeout":
                        results.append(f"test_{idx:02d} [TIMEOUT] {execution_time:.2f}ms")
                        raise TimeoutError("Test case exceeded time limit")
                    
                    if result == expected_output:
                        results.append(f"test_{idx:02d} [PASS] {execution_time:.2f}ms")
                        passed_tests += 1
                    else:
                        results.append(f"test_{idx:02d} [FAIL] {execution_time:.2f}ms")
                except Exception as e:
                    end_time = time.time()
                    execution_time = (end_time - start_time) * 1000  # in milliseconds
                    results.append(f"test_{idx:02d} [ERROR] {execution_time:.2f}ms - {e}")
                    raise e  # Propagate the error to handle in outer except block

        except Exception as e:
            results.append(f"Compilation or Execution Error: {e}")
            passed_tests = 0
            total_tests = len(self.test_cases)

        score = Decimal((passed_tests / total_tests) * 100).quantize(Decimal('0.00')) if total_tests > 0 else Decimal('0.00')
        results.append(f"> {passed_tests}/{total_tests} tests passed")
        return passed_tests, total_tests, score, results

if __name__ == "__main__":
    pdf_name = "Sum2.pdf"
    solution_file = "solution.py"  # Replace with the path to the solution file
    grader = AutoGrader(pdf_name, solution_file)
    passed_tests, total_tests, score, results = grader.grade()
    for result in results:
        print(result)
    print(f"Passed {passed_tests}/{total_tests} tests. Score: {score}%")
