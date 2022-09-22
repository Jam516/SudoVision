import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode
import pandas as pd
from requests import get, post
import time
import datetime
import json

HEADER = {"x-dune-api-key" : st.secrets["API_KEY"]}
BASE_URL = "https://api.dune.com/api/v1/"
solved = 0

def make_api_url(module, action, ID):
    """
    We shall use this function to generate a URL to call the API.
    """

    url = BASE_URL + module + "/" + ID + "/" + action

    return url

def execute_query():
    """
    Takes in the query ID.
    Calls the API to execute the query.
    Returns the execution ID of the instance which is executing the query.
    """

    url = make_api_url("query", "execute", '1295309')
    # datas = {"query_parameters": { "Creator Address":address}}
    response = post(url, headers=HEADER)
    # , data=json.dumps(datas)
    execution_id = response.json()['execution_id']

    return execution_id

def get_query_status(execution_id):
    """
    Takes in an execution ID.
    Fetches the status of query execution using the API
    Returns the status response object
    """

    url = make_api_url("execution", "status", execution_id)
    response = get(url, headers=HEADER)

    return response

def get_query_results(execution_id):
    """
    Takes in an execution ID.
    Fetches the results returned from the query using the API
    Returns the results response object
    """

    url = make_api_url("execution", "results", execution_id)
    response = get(url, headers=HEADER)

    return response


def aggrid_interactive_table(df: pd.DataFrame):
    """Creates an st-aggrid interactive table based on a dataframe.

    Args:
        df (pd.DataFrame]): Source dataframe

    Returns:
        dict: The selected row
    """
    options = GridOptionsBuilder.from_dataframe(
        df, enableRowGroup=True, enableValue=True, enablePivot=True
    )

    options.configure_side_bar()

    options.configure_selection("single")
    selection = AgGrid(
        df,
        enable_enterprise_modules=True,
        gridOptions=options.build(),
        theme="streamlit",
        update_mode=GridUpdateMode.MODEL_CHANGED,
        allow_unsafe_jscode=True,
    )

    return selection

################## Visuals #########################

st.title('SudoSwap Pool Analysis')

'Enter the address you used to create your pool'

owner = st.text_input('Pool Owner Address', '0xf4f9e8cdae4b69ff3e0beca0dff65b9b718c3161')

ct = execute_query()

while solved == 0:
    response = get_query_status(ct)
    state = response.json()['state']
    if state == 'QUERY_STATE_COMPLETED':
        solved = 1
    else:
        time.sleep(2)
# solved = 0

pools = get_query_results(ct)
pools = pd.DataFrame(pools.json()['result']['rows'])
pool = pools[pools['creator_address'] == owner.lower()]
pools.rename(columns={'pool_address': 'Pool Address'
    , 'nftcontractaddress' : 'NFT Contract'
    , 'creator_address' : 'Creator'
    , 'owner_fee_volume_eth': 'Fees Earned'
    , 'eth_balance': 'ETH Balance'
    , 'nft_balance': 'NFT Balance'
    , 'eth_volume': 'Trading Volume (ETH)'
    , 'usd_volume': 'Trading Volume (USD)'
    , 'nfts_traded': 'NFTs Traded'
    , 'spotprice': 'Spot Price'
    , 'delta': 'Delta'
    , 'pooltype': 'Pool Type'
    , 'pricing_type': 'Pricing Type'

    , 'initial_eth': 'Initial ETH'
    , 'initial_nft_count': 'Initial NFTs'
    , 'initial_price': 'Initial Spot Price'
    , 'days_passed': 'Age (Days)'
    , 'eth_change_trading': 'Inventory Change By Trading (ETH)'
    , 'nft_change_trading': 'Inventory Change By Trading (NFTs)'}, inplace=True)

pooltable = pools[['Pool Address',
            'Fees Earned',
            'ETH Balance',
            'NFT Balance',
            'Trading Volume (ETH)',
            'Trading Volume (USD)',
            'NFTs Traded',
            'Spot Price',
            'Delta',
            'Pool Type',
            'Pricing Type']]

pooldetails = pools[['Pool Address',
            'NFT Contract',
            'ETH Balance',
            'NFT Balance',
            'Spot Price',
            'Initial ETH',
            'Initial NFTs',
            'Initial Spot Price',
            'Inventory Change By Trading (ETH)',
            'Inventory Change By Trading (NFTs)',
            'Age (Days)',
            'Trading Volume (ETH)',
            'Fees Earned']]

pooldetails['Manual Inventory Change (ETH)'] = pooldetails['ETH Balance'] - pooldetails['Initial ETH'] - pooldetails['Inventory Change By Trading (ETH)']
pooldetails['Manual Inventory Change (NFTs)'] = pooldetails['NFT Balance'] - pooldetails['Initial NFTs'] - pooldetails['Inventory Change By Trading (NFTs)']
pooldetails['Current Inventory Value'] = pooldetails['ETH Balance'] + (pooldetails['NFT Balance'] * pooldetails['Spot Price'])
pooldetails['Inventory Value If Held'] = pooldetails['Initial ETH'] + pooldetails['Manual Inventory Change (ETH)'] + ((pooldetails['Initial NFTs']+pooldetails['Manual Inventory Change (NFTs)']) * pooldetails['Spot Price'])
pooldetails['Impermanent Loss'] = pooldetails['Current Inventory Value'] - pooldetails['Inventory Value If Held']

# pooldetails = pooldetails[['Pool Address',
#             'NFT Contract',
#             'ETH Balance',
#             'NFT Balance',
#             'Spot Price',
#
#             'Initial ETH',
#             'Initial NFTs',
#             'Initial Spot Price',
#
#             'Manual Inventory Change (ETH)',
#             'Manual Inventory Change (NFTs)',
#
#             'Inventory Change By Trading (ETH)',
#             'Inventory Change By Trading (NFTs)',
#
#             'Current Inventory Value',
#             'Inventory Value If Held',
#             'Impermanent Loss',
#
#             'Age (Days)',
#             'Trading Volume (ETH)',
#             'Fees Earned']]

selection = aggrid_interactive_table(df=pooltable)
# st.table(df)

st.write("Select a row to see pool specific stats:")
if selection["selected_rows"]:
    stats = pooldetails[pooldetails['Pool Address'] == selection["selected_rows"][0]["Pool Address"]]
    # st.json(stats.to_json(orient = 'records'))
    st.dataframe(stats.T)
