import requests
import json
from weds import webflow_bearer_token
from statistics import mean, median

def fetch_items(collection_id, offset=0):
    url = f"https://api.webflow.com/v2/collections/{collection_id}/items?limit=100&offset={offset}"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {webflow_bearer_token}"
    }
    response = requests.get(url, headers=headers)
    return json.loads(response.text)

def fetch_mobiloperators():
    url = "https://api.webflow.com/v2/collections/6662d0070fad018b334db523/items"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {webflow_bearer_token}"
    }
    response = requests.get(url, headers=headers)
    data = json.loads(response.text)
    return {item['id']: {'name': item['fieldData']['name'], 'slug': item['fieldData']['slug']} for item in data['items']}

def update_stats(bedriftsabonnement_count, mobiloperator_count, paragraph, avg_price_10, avg_price_100):
    url = "https://api.webflow.com/v2/collections/66b37bc089a0b960e7a6d238/items/66b37c4de7d06b0419b3a02c"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {webflow_bearer_token}"
    }
    payload = {
        "fieldData": {
            "name": "Stats",
            "slug": "stats",
            "antall-avtaler": str(bedriftsabonnement_count),
            "antall-operatorer": str(mobiloperator_count),
            "paragraf-billig-dyr": f"<p>{paragraph}</p>",
            "avg-price-10": str(avg_price_10),
            "avg-price-100": str(avg_price_100)
        }
    }
    response = requests.patch(url, json=payload, headers=headers)
    return response.json()

def process_items():
    offset = 0
    bedriftsabonnement_count = 0
    mobiloperator_prices = {}
    prices_10gb = []
    prices_100gb = []
    mobiloperator_names = fetch_mobiloperators()

    while True:
        data = fetch_items("6660c15ec77f5270c0a534d2", offset)
        items = data.get('items', [])
        
        if not items:
            break

        for item in items:
            if item['fieldData'].get('bedriftsabonnement', False):
                bedriftsabonnement_count += 1
                mobiloperator = item['fieldData'].get('mobiloperator')
                price = item['fieldData'].get('pris')
                mobildata = item['fieldData'].get('mobildata')
                
                if mobiloperator and price:
                    if mobiloperator not in mobiloperator_prices:
                        mobiloperator_prices[mobiloperator] = []
                    mobiloperator_prices[mobiloperator].append(price)
                
                if mobildata == '10' and price:
                    prices_10gb.append(price)
                elif mobildata == '100' and price:
                    prices_100gb.append(price)

        offset += 100

    # Calculate average prices
    avg_prices = {op: mean(prices) for op, prices in mobiloperator_prices.items()}
    cheapest_op = min(avg_prices, key=avg_prices.get)
    most_expensive_op = max(avg_prices, key=avg_prices.get)

    # Calculate percentage difference
    price_diff_percent = ((avg_prices[most_expensive_op] - avg_prices[cheapest_op]) / avg_prices[most_expensive_op]) * 100

    # Create the paragraph with linked company names
    cheapest_op_link = f'<a href="/mobiltelefoni/mobilabonnement/{mobiloperator_names[cheapest_op]["slug"]}">{mobiloperator_names[cheapest_op]["name"]}</a>'
    most_expensive_op_link = f'<a href="/mobiltelefoni/mobilabonnement/{mobiloperator_names[most_expensive_op]["slug"]}">{mobiloperator_names[most_expensive_op]["name"]}</a>'

    paragraph = (f"Mobiloperatøren {cheapest_op_link} er den som har de billigste avtalene på bedriftsabonnement, "
                 f"de er faktisk {price_diff_percent:.1f}% billigere enn den dyreste leverandøren på bedriftstelefoni "
                 f"som er {most_expensive_op_link}.")

    # Calculate median prices for 10GB and 100GB
    avg_price_10 = median(prices_10gb) if prices_10gb else 0
    avg_price_100 = median(prices_100gb) if prices_100gb else 0

    print(f"Number of contracts with 'bedriftsabonnement' set to true: {bedriftsabonnement_count}")
    print(f"Number of unique 'mobiloperator' offering 'bedriftsabonnement': {len(mobiloperator_prices)}")
    print(f"Paragraph: {paragraph}")
    print(f"Median price for 10GB: {avg_price_10}")
    print(f"Median price for 100GB: {avg_price_100}")

    # Update the stats in Webflow
    update_result = update_stats(bedriftsabonnement_count, len(mobiloperator_prices), paragraph, avg_price_10, avg_price_100)
    print("Update result:", update_result)

if __name__ == "__main__":
    process_items()