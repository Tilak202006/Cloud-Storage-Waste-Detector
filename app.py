
import streamlit as st
import boto3
from botocore.exceptions import ClientError, BotoCoreError

# -------------------------------
# PAGE CONFIGURATION
# -------------------------------

st.set_page_config(
    page_title="Cloud Storage Waste Detector",
    page_icon="☁️",
    layout="wide"
)

# -------------------------------
# TITLE
# -------------------------------

st.title("☁️ Cloud Storage Waste Detector")
st.markdown("Identify duplicate files and potential storage waste.")

# -------------------------------
# AWS CONFIGURATION
# -------------------------------

REGION = "ap-southeast-2"
TABLE_NAME = "CloudWasteMetadata"


# -------------------------------
# LOAD DATA FROM DYNAMODB
# -------------------------------

@st.cache_data(ttl=30)
def load_files():

    dynamodb = boto3.resource(
        "dynamodb",
        region_name=REGION
    )

    table = dynamodb.Table(TABLE_NAME)

    items = []

    response = table.scan()
    items.extend(response.get("Items", []))

    while "LastEvaluatedKey" in response:

        response = table.scan(
            ExclusiveStartKey=response["LastEvaluatedKey"]
        )

        items.extend(response.get("Items", []))

    return items


# -------------------------------
# MAIN DASHBOARD
# -------------------------------

try:

    with st.spinner("Connecting to AWS DynamoDB..."):
        files = load_files()

    st.success("Connected to AWS DynamoDB successfully!")

    # Calculate statistics

    total_files = len(files)

    duplicate_files = [
        file for file in files
        if file.get("is_duplicate", False)
    ]

    total_storage = sum(
        int(file.get("size_bytes", 0))
        for file in files
    )

    # -------------------------------
    # DASHBOARD METRICS
    # -------------------------------

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Files",
        total_files
    )

    col2.metric(
        "Duplicate Files",
        len(duplicate_files)
    )

    col3.metric(
        "Total Storage",
        f"{total_storage} bytes"
    )

    # -------------------------------
    # FILE DETAILS
    # -------------------------------

    st.subheader("File Details")

    for file in sorted(
        files,
        key=lambda x: x.get("file_key", "")
    ):

        filename = file.get("file_key", "Unknown file")

        with st.expander(filename):

            st.markdown(f"**File Name:** {filename}")

            st.markdown(
                f"**File Size:** {file.get('size_bytes', 0)} bytes"
            )

            st.markdown(
                f"**SHA256:** {file.get('sha256', 'N/A')}"
            )

            st.markdown(
                f"**Last Modified:** {file.get('last_modified', 'N/A')}"
            )

            if file.get("is_duplicate", False):

                st.error(
                    f"Duplicate of: {file.get('duplicate_of', 'Unknown')}"
                )

            else:

                st.success("No duplicate detected")

    # -------------------------------
    # DUPLICATE FILE ANALYSIS
    # -------------------------------

    st.subheader("Duplicate File Analysis")

    if duplicate_files:

        for file in duplicate_files:

            st.warning(
                f"{file.get('file_key')} is a duplicate of "
                f"{file.get('duplicate_of')}"
            )

    else:

        st.info("No duplicate files found.")

    # -------------------------------
    # REFRESH BUTTON
    # -------------------------------

    if st.button("Refresh Dashboard"):

        st.cache_data.clear()
        st.rerun()


# -------------------------------
# ERROR HANDLING
# -------------------------------

except (ClientError, BotoCoreError) as error:

    st.error(f"AWS connection error: {error}")

except Exception as error:

    st.error(f"Unexpected error: {error}")
