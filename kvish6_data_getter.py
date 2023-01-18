import requests
import logging

logger = logging.getLogger(__name__)


def get_kvish6_invoices(tz, plate):
    try:
        session = requests.Session()
        # First POST request
        url = "https://service.kvish6.co.il/api/Payment/paymentLogin"
        payload = {
            "CustomerId": tz,
            "IdMeanCode": 2,
            "IdMeanValue": plate,
            "gRecaptchaResponse": ""
        }
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,he;q=0.6,de;q=0.5",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "DNT": "1",
            "Host": "service.kvish6.co.il",
            "Origin": "https://service.kvish6.co.il",
            "Referer": "https://service.kvish6.co.il/",
            "sec-ch-ua": '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "macOS",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }
        response = session.post(url, json=payload, headers=headers)
        logger.debug(response.content)

        # Get Token from response
        data = response.json()
        token = data["Payload"]["Token"]

        # Second POST request
        url = "https://service.kvish6.co.il/api/Payment/getCustOpenInvoices"
        payload = {"Token": token}
        response = session.post(url, json=payload, headers=headers)
        
        logger.debug(response.content)
        
        data = response.json()
        open_invoices = data["Payload"]["openInvoices"]

        if len(open_invoices) == 0:
            return "You have no invoices to pay."
        else:
            return f"You have {len(open_invoices)} invoices to pay."
    except (requests.exceptions.HTTPError, ValueError):
        return "Something went wrong during data processing"
