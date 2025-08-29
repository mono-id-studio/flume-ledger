def print_test_info(
    test_name: str, test_description: str, input_data: dict, expected_result: str
):
    print(f"\n{test_name}: {test_description}\n")
    print_input_data(input_data)
    print(f"Expected result: {expected_result}")


def print_input_data(input_data: dict):
    for key, value in input_data.items():
        if isinstance(value, dict):
            print(
                f"{key} dictionary ----------------------------------------------------------------------\n"
            )
            print_input_data(value)
        elif isinstance(value, list):
            print(
                f"{key} list ----------------------------------------------------------------------\n"
            )
            for item in value:
                print(f"  {item}\n")
        elif isinstance(value, str):
            print(f"{key}: {value}\n")
        elif isinstance(value, object):
            print(
                f"{key} object ----------------------------------------------------------------------\n"
            )
            for k, v in value.__dict__.items():
                print(f"{key}.{k}: {v}\n")
        else:
            print(f"{key}: {value}\n")


def print_test_result(test_name: str, test_result: str, actual_result: str):
    print(f"\n{test_name}: {test_result}\n")
    print(f"Actual result: {actual_result}")
