"""
Test loading datasets into the sandbox (avoiding volume sync issues).

This test verifies that we can load files both from the api and from S3
into the sandbox

It also verifies thaat loading more than one dataset in the same session works (this raised 
problems in the past).
"""

import os
import base64
import pytest
import time
from dotenv import load_dotenv
from backend.modal_runtime.executor import SandboxExecutor
from backend.opendata_api.init_client import client
from backend.opendata_api.helpers import get_dataset_bytes
import modal


# ===== helpers =====
# Lookup deployed Modal functions (using from_name)
def _get_modal_function(name: str):
    """Get a deployed Modal function by name."""
    try:
        return modal.Function.from_name("lg-urban-executor", name)
    except Exception:
        # Fallback to import for local development
        raise Exception(f"Modal function {name} not found")

list_loaded_datasets_func = _get_modal_function("list_loaded_datasets")
write_dataset_bytes_func = _get_modal_function("write_dataset_bytes")

load_dotenv()

# we need to check that the tokens and bucket are configured before running the tests
def check_modal_tokens():
    """Check that Modal tokens are configured."""
    if not (os.getenv("MODAL_TOKEN_ID") and os.getenv("MODAL_TOKEN_SECRET")):
        raise ValueError("Modal tokens not configured")

def check_s3_bucket():
    """Check that S3 bucket is configured."""
    if not os.getenv("S3_BUCKET") or not os.getenv("AWS_ACCESS_KEY_ID") or not os.getenv("AWS_SECRET_ACCESS_KEY") or not os.getenv("AWS_REGION"):
        raise ValueError("S3 bucket not configured")

# --- fixtures ---
@pytest.fixture(scope="module")
def test_session_id():
    """Create a single test session ID shared across all tests in this module."""
    session_id = "test-load-to-sandbox-session"
    yield session_id
    # Cleanup: terminate executor if created
    print(f"\n🧹 Cleaning up test session: {session_id}")
    from backend.graph.tools.sandbox_tools import terminate_session_executor, _executor_cache
    terminate_session_executor(session_id)
    _executor_cache.pop(session_id, None)


@pytest.fixture(scope="module")
def test_executor(test_session_id):
    """Create a single executor shared across all tests in this module."""
    check_modal_tokens()  # Check before creating executor
    executor = SandboxExecutor(session_id=test_session_id)
    yield executor
    executor.terminate()

# --- actual tests ---
@pytest.mark.asyncio
async def test_load_dataset_from_api(test_executor, test_session_id):
    """Test that we can export a dataset by running export code inside the sandbox."""
    executor = test_executor
    session_id = test_session_id
    print(f"Session ID 1: {session_id}")

    dataset_id = "temperature_bologna"
    bytes = await get_dataset_bytes(client=client, dataset_id=dataset_id)
    b64 = base64.b64encode(bytes).decode("ascii")
    res = write_dataset_bytes_func.remote(dataset_id="temperature_bologna", data_b64=b64, session_id=session_id, ext="parquet")

    assert res["dataset_id"] == "temperature_bologna"
    assert res["rel_path"].endswith("datasets/temperature_bologna.parquet")
    
    # Poll for volume sync by checking directly in the sandbox
    max_wait = 20  # seconds
    start = time.time()
    file_found = False
    rel_path = res["rel_path"]
    while time.time() - start < max_wait:
        check_code = f"""
import os
path = '{rel_path}'
exists = os.path.exists(path)
print(f"File exists: {{exists}}")
if exists:
    size = os.path.getsize(path)
    print(f"File size: {{size}} bytes")
"""
        result = executor.execute(check_code)
        if "File exists: True" in result.get("stdout", ""):
            file_found = True
            print(f"File found in sandbox after {time.time() - start:.1f} seconds")
            break
        time.sleep(1)
    
    if not file_found:
        raise TimeoutError(f"File '{rel_path}' not found in sandbox after {max_wait}s")

    print("Loaded dataset from API successfully: ", res)

    # then test that the sandbox can access the dataset in code
    
    code = f"""
import pandas as pd
df = pd.read_parquet('{res["rel_path"]}')
print(f"Loaded dataset with shape: {{df.shape}}")
print(f"Columns: {{list(df.columns)}}")
print(f"First few rows:")
print(df.head())
"""
    result = executor.execute(code)
        
    assert "stdout" in result
    assert "shape" in result["stdout"].lower() or "Loaded dataset" in result["stdout"]
    assert not result.get("stderr") or result["stderr"] == ""
    
    print("Loaded dataset from API and accessed from sandbox successfully")

@pytest.mark.asyncio
async def test_load_dataset_from_s3(test_executor, test_session_id):
    """Test that we can load a dataset from S3 into the sandbox."""
    check_s3_bucket()

    executor = test_executor
    session_id = test_session_id
    print(f"Session ID 2: {session_id}")
    
    # Download from S3
    import boto3
    from botocore.client import Config
    region = os.getenv("AWS_REGION", "eu-central-1")
    s3 = boto3.client(
        "s3",
        region_name=region,
        config=Config(signature_version='s3v4')
    )
    input_bucket = os.getenv("S3_BUCKET")
    s3_key = f"input/datasets/alberi-manutenzioni.parquet"
    s3.head_object(Bucket=input_bucket, Key=s3_key)
    data_bytes = s3.get_object(Bucket=input_bucket, Key=s3_key)["Body"].read()

    # Load these bytes into the sandbox
    b64 = base64.b64encode(data_bytes).decode("ascii")
    res = write_dataset_bytes_func.remote(dataset_id="alberi-manutenzioni", data_b64=b64, session_id=session_id, ext="parquet")

    assert res["dataset_id"] == "alberi-manutenzioni"
    assert res["rel_path"].endswith("datasets/alberi-manutenzioni.parquet")
    
    # Poll for volume sync by checking directly in the sandbox
    max_wait = 20
    start = time.time()
    file_found = False
    rel_path = res["rel_path"]
    while time.time() - start < max_wait:
        check_code = f"""
import os
path = '{rel_path}'
exists = os.path.exists(path)
print(f"File exists: {{exists}}")
if exists:
    size = os.path.getsize(path)
    print(f"File size: {{size}} bytes")
"""
        result = executor.execute(check_code)
        if "File exists: True" in result.get("stdout", ""):
            file_found = True
            print(f"File found in sandbox after {time.time() - start:.1f} seconds")
            break
        time.sleep(1)
    
    if not file_found:
        raise TimeoutError(f"File '{rel_path}' not found in sandbox after {max_wait}s")

    # Test that sandbox can read it
    code = f"""
import pandas as pd
df = pd.read_parquet('{res["rel_path"]}')
print(f"Dataset shape: {{df.shape}}")
print(f"Memory usage: {{df.memory_usage(deep=True).sum() / 1024**2:.2f}} MB")
"""
    result = executor.execute(code)
    
    assert "Dataset shape" in result["stdout"]
    assert not result.get("stderr") or result["stderr"] == ""

@pytest.mark.asyncio
async def test_load_multiple_datasets_in_same_session(test_executor, test_session_id):
    """Test that we can load multiple datasets into the sandbox in the same session. Use api for simplicity"""
    executor = test_executor
    session_id = test_session_id
    print(f"Session ID 3: {session_id}")

    dataset_id1 = "temperature_bologna"
    bytes = await get_dataset_bytes(client=client, dataset_id=dataset_id1)
    b64 = base64.b64encode(bytes).decode("ascii")
    res1 = write_dataset_bytes_func.remote(dataset_id="temperature_bologna", data_b64=b64, session_id=session_id, ext="parquet")
    
    assert res1["dataset_id"] == dataset_id1
    assert res1["rel_path"].endswith(f"datasets/{dataset_id1}.parquet")
    
    # Poll for first dataset by checking directly in the sandbox
    max_wait = 20
    start = time.time()
    file1_found = False
    rel_path1 = res1["rel_path"]
    while time.time() - start < max_wait:
        check_code = f"""
import os
path = '{rel_path1}'
exists = os.path.exists(path)
print(f"File 1 exists: {{exists}}")
"""
        result = executor.execute(check_code)
        if "File 1 exists: True" in result.get("stdout", ""):
            file1_found = True
            print(f"File 1 found in sandbox after {time.time() - start:.1f} seconds")
            break
        time.sleep(1)
    
    assert file1_found, f"File {rel_path1} not found in sandbox after {max_wait}s"

    dataset_id2 = "precipitazioni_bologna"
    bytes = await get_dataset_bytes(client=client, dataset_id=dataset_id2)
    b64 = base64.b64encode(bytes).decode("ascii")
    res2 = write_dataset_bytes_func.remote(dataset_id=dataset_id2, data_b64=b64, session_id=session_id, ext="parquet")
    
    assert res2["dataset_id"] == dataset_id2
    assert res2["rel_path"].endswith(f"datasets/{dataset_id2}.parquet")
    
    # Poll for second dataset by checking directly in the sandbox
    start = time.time()
    file2_found = False
    rel_path2 = res2["rel_path"]
    while time.time() - start < max_wait:
        check_code = f"""
import os
path = '{rel_path2}'
exists = os.path.exists(path)
print(f"File 2 exists: {{exists}}")
"""
        result = executor.execute(check_code)
        if "File 2 exists: True" in result.get("stdout", ""):
            file2_found = True
            print(f"File 2 found in sandbox after {time.time() - start:.1f} seconds")
            break
        time.sleep(1)
    
    assert file2_found, f"File {rel_path2} not found in sandbox after {max_wait}s"

    # List the datasets in the volume
    files = list_loaded_datasets_func.remote(session_id=session_id)
    names = {f.get("path") for f in files}
    assert f"{dataset_id1}.parquet" in names
    assert f"{dataset_id2}.parquet" in names

    # check that the sandbox can access both datasets in code
    code = f"""
import pandas as pd
df1 = pd.read_parquet('{res1["rel_path"]}')
df2 = pd.read_parquet('{res2["rel_path"]}')
print(f"Dataset 1 shape: {{df1.shape}}")
print(f"Dataset 2 shape: {{df2.shape}}")
print("Both datasets loaded successfully!")
"""

    result = executor.execute(code)
    assert "stdout" in result
    assert "shape" in result["stdout"].lower() or "Loaded dataset" in result["stdout"]
    assert not result.get("stderr") or result["stderr"] == ""