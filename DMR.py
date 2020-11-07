import requests, re
from flask import Flask, jsonify
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route("/api/<string:nrplate>", methods=["GET"])
def request_data(nrplate):
    def get_data(plate:str):
        def get_token(session):
            r = session.get("https://motorregister.skat.dk/dmr-front/dmr.portal?_nfpb=true&_nfpb=true&_pageLabel=vis_koeretoej_side&_nfls=false")
            soup = BeautifulSoup(r.text, features="html.parser")
            try:
                return soup.find('input', {'name': 'dmrFormToken'})['value']
            except (TypeError, KeyError):
                return None
        session = requests.Session()
        token = get_token(session)
        if token is None:
            # Script can not go anywhere without the dmrFormToken
            return {"error":"dmrFormToken could not be found."}

        payload = {"dmrFormToken": token,
                "kerne_vis_koeretoej{actionForm.soegeord}": plate,
                "kerne_vis_koeretoejwlw-radio_button_group_key:{actionForm.soegekriterie}": "REGISTRERINGSNUMMER"}
        r = session.post('https://motorregister.skat.dk/dmr-front/dmr.portal?_nfpb=true&_windowLabel=kerne_vis_koeretoej&kerne_vis_koeretoej_actionOverride=%2Fdk%2Fskat%2Fdmr%2Ffront%2Fportlets%2Fkoeretoej%2Fnested%2FfremsoegKoeretoej%2Fsearch&_pageLabel=vis_koeretoej_side', data=payload)
        soup = BeautifulSoup(r.text, features="html.parser")
        if "Ingen køretøjer fundet." in r.text:
            # Not a valid license plate
            return {"error":"Not a valid licenseplate."}
        vehicle = soup.find_all("div", {"class":"notrequired keyvalue singleDouble"})
        data = dict({"køretøj":{}})

        # KØRETØJ + REGISTRERINGSFORHOLD
        for div in vehicle:
            spans = div.find_all("span")
            try:
                span0 = spans[0].text.lower()
                span0 = span0.replace(":", "")
            except:
                pass
            
            if span0 == "registrerings\xadnummer":
                span0 = "registreringsnummer"
            elif span0 == "første registrerings\xaddato":
                span0 = "første registreringsdato"
            else:
                pass

            if span0 == "mærke, model, variant":
                mærke, model, variant = spans[1].text.split(",")
                data["køretøj"]["mærke"] = mærke
                data["køretøj"]["model"] = model.strip()
                data["køretøj"]["variant"] = variant.strip()
            else:
                data["køretøj"][span0] = spans[1].text
        return data
    return jsonify(get_data(nrplate))

@app.route("/api/", methods=["GET"])
def api():
    return jsonify({"error":"No numberplate was given."})

if __name__ == "__main__":
    app.run()