import json

with open("messages_train.json", "r", encoding="utf-8") as file:
    data = json.load(file)

domains = ["electrician", "tailor", "tiffin", "baker"]

for domain in domains:
    print("\n" + "=" * 60)
    print("DOMAIN:", domain.upper())
    print("=" * 60)

    count = 0

    for item in data:
        if item["domain"] == domain:
            print("\nID:", item["id"])
            print("MESSAGE:", item["message"])
            print("EXPECTED:", item["expected"])

            count += 1

            # Har domain ke sirf pehle 3 examples
            if count == 3:
                break