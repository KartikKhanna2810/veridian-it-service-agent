from agent.core import run_agent


test_cases = [
    {
        "employee": "Sanjay Oberoi",
        "email": "sanjay.oberoi@veridian-corp.example",
        "message": "My VPN stopped working this morning, says credentials expired."
    },
    {
        "employee": "Ananya Reddy",
        "email": "ananya.reddy@veridian-corp.example",
        "message": "I think I got a phishing email asking for my login."
    },
    {
        "employee": "Vikram Chawla",
        "email": "vikram.chawla@veridian-corp.example",
        "message": "Can I get Wi-Fi access for a guest tomorrow?"
    },
    {
        "employee": "Rahul Menon",
        "email": "rahul.menon@veridian-corp.example",
        "message": "hey can you help, its not working"
    }
]


for test in test_cases:

    print("\n" + "=" * 70)

    print("EMPLOYEE:")
    print(test["employee"])

    print("MESSAGE:")
    print(test["message"])

    result = run_agent(
        message=test["message"],
        employee=test["employee"],
        email=test["email"]
    )

    print("\nISSUE TYPE:")
    print(result["issue_type"])

    print("\nDECISION:")
    print(result["decision"])

    print("\nPRIORITY:")
    print(result["priority"])

    print("\nRESPONSE:")
    print(result["response"])

    print("\nNEXT ACTION:")
    print(result["next_action"])

    print("\nSOURCES:")
    print(
        ", ".join(result["sources"])
        if result["sources"]
        else "NONE"
    )

    print("\nRELATED TICKETS:")
    for ticket in result["related_tickets"]:
        print(
            f"{ticket['ticket_id']} - "
            f"{ticket['issue_summary']} - "
            f"{ticket['status']}"
        )

    print("\nCREATED TICKET:")
    print(result["ticket_id"] or "No ticket created")

    print("\nAUDIT ID:")
    print(result["audit_id"])

    print("=" * 70)