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

def make_api_url(module, action, ID):
    """
    We shall use this function to generate a URL to call the API.
    """

    url = BASE_URL + module + "/" + ID + "/" + action

    return url

def execute_query(address):
    """
    Takes in the query ID.
    Calls the API to execute the query.
    Returns the execution ID of the instance which is executing the query.
    """

    url = make_api_url("query", "execute", '1362901')
    datas = {"query_parameters": { "Creator Address":address}}
    response = post(url, headers=HEADER, data=json.dumps(datas))

    execution_id = response.json()['execution_id']

    return execution_id

def execute_query2(address):
    """
    Takes in the query ID.
    Calls the API to execute the query.
    Returns the execution ID of the instance which is executing the query.
    """

    url = make_api_url("query", "execute", '1392569')
    datas = {"query_parameters": { "Pool Address":address}}
    response = post(url, headers=HEADER, data=json.dumps(datas))

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

def loading_loop(query):
    solved = 0
    while solved == 0:
        response = get_query_status(query)
        state = response.json()['state']
        if state == 'QUERY_STATE_COMPLETED':
            solved = 1
        else:
            time.sleep(1)
    return get_query_results(query)


################## Visuals #########################

st.title('SudoSwap Pool Analysis')

'Enter the address you used to create your pool'

owner = st.text_input('Pool Owner Address', '0x50664ede715e131f584d3e7eaabd7818bb20a068')

ct = execute_query(owner)

pools = loading_loop(ct)
pools = pd.DataFrame(pools.json()['result']['rows'])
# pool = pools[pools['creator_address'] == owner.lower()]
pools.rename(columns={'pool_address': 'Pool Address'
    , 'nft_contract_address' : 'NFT Contract'
    # , 'creator_address' : 'Creator'
    , 'pool_fee_volume_eth': 'Fees Earned'
    , 'eth_balance': 'ETH Balance'
    , 'nft_balance': 'NFT Balance'
    , 'eth_volume': 'Trading Volume (ETH)'
    , 'usd_volume': 'Trading Volume (USD)'
    , 'nfts_traded': 'NFTs Traded'
    , 'spot_price': 'Spot Price'
    , 'delta': 'Delta'
    , 'bonding_curve': 'Bonding Curve'
    , 'pool_type': 'Pool Type'

    , 'initial_eth_balance': 'Initial ETH'
    , 'initial_nft_balance': 'Initial NFTs'
    , 'initial_spot_price': 'Initial Spot Price'
    , 'creation_block_time': 'Creation Time'
    , 'eth_change_trading': 'Inventory Change By Trading (ETH)'
    , 'nft_change_trading': 'Inventory Change By Trading (NFTs)'}, inplace=True)

pools['Manual Inventory Change (ETH)'] = pools['ETH Balance'] - pools['Initial ETH'] - pools['Inventory Change By Trading (ETH)']
pools['Manual Inventory Change (NFTs)'] = pools['NFT Balance'] - pools['Initial NFTs'] - pools['Inventory Change By Trading (NFTs)']
pools['Current Inventory Value'] = pools['ETH Balance'] + (pools['NFT Balance'] * pools['Spot Price'])
pools['Inventory Value If Held'] = pools['Initial ETH'] + pools['Manual Inventory Change (ETH)'] + ((pools['Initial NFTs']+pools['Manual Inventory Change (NFTs)']) * pools['Spot Price'])
pools['Impermanent Loss'] = pools['Inventory Value If Held'] - pools['Current Inventory Value']
pools['Creation Time'] = pools['Creation Time'].str[:10]
pools['Today'] = pd.to_datetime("now")
pools['Creation Time'] = pd.to_datetime(pools['Creation Time'])
pools['Age'] = (pools['Today'] - pools['Creation Time'])

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
            'Bonding Curve']]

# pooldetails = pools[['Pool Address',
#             'NFT Contract',
#             'ETH Balance',
#             'NFT Balance',
#             'Spot Price',
#             'Initial ETH',
#             'Initial NFTs',
#             'Initial Spot Price',
#             'Inventory Change By Trading (ETH)',
#             'Inventory Change By Trading (NFTs)',
#             'Creation Time',
#             'Trading Volume (ETH)',
#             'Fees Earned']]

pooldetails = pools[['Pool Address',
            'NFT Contract',
            'ETH Balance',
            'NFT Balance',
            'Spot Price',

            'Initial ETH',
            'Initial NFTs',
            'Initial Spot Price',

            'Manual Inventory Change (ETH)',
            'Manual Inventory Change (NFTs)',

            'Inventory Change By Trading (ETH)',
            'Inventory Change By Trading (NFTs)',

            'Current Inventory Value',
            'Inventory Value If Held',
            'Impermanent Loss',

            'Age',
            'Trading Volume (ETH)',
            'Fees Earned']]

selection = aggrid_interactive_table(df=pooltable)
# st.table(df)

st.write("**Select a row to see pool specific stats:**")
if selection["selected_rows"]:
    stats = pooldetails[pooldetails['Pool Address'] == selection["selected_rows"][0]["Pool Address"]]

    earn = execute_query2(selection["selected_rows"][0]["Pool Address"])

    earnings = loading_loop(earn)
    earnings = pd.DataFrame(earnings.json()['result']['rows'])
    earnings.rename(columns={'daily_fees': 'Fees Earned (ETH)', 'day' : 'Day'}, inplace=True)
    earnings['Day'] = earnings['Day'].str[:10]
    earnings['Day']= pd.to_datetime(earnings['Day'])

    ''
    '**Pool Earnings Over Time**'
    st.bar_chart(data=earnings, y='Fees Earned (ETH)', x='Day')

    st.table(stats.T)
