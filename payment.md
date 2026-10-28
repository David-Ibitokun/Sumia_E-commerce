**Steps required to add a payment gateway**

1. **Choose a provider**
   - For Nigerian Naira payments, consider Paystack or Flutterwave.
   - Create a merchant account and obtain test/live API keys.

2. **Install the provider SDK**
   - Add the gateway package to `requirements.txt`, or use Django’s HTTP client/API.

3. **Add environment variables**
   - Store keys in `.env`, never in source code:
   ```env
   PAYMENT_PUBLIC_KEY=
   PAYMENT_SECRET_KEY=
   PAYMENT_WEBHOOK_SECRET=
   ```

4. **Update Django settings**
   - Load the gateway configuration in `settings.py`.

5. **Update the order model**
   - Add fields such as:
     - `payment_reference`
     - `payment_status`
     - `paid_at`
     - `gateway_response`
   - Add a migration.

6. **Change order creation logic**
   - In `orders.py`, do not set `is_paid=True` merely because the selected method is not COD.
   - Create the order as unpaid or pending until the gateway confirms payment.

7. **Create a payment initialization service**
   - Calculate the amount server-side.
   - Generate a unique payment reference.
   - Send the customer to the provider’s hosted payment page or initialize the provider checkout.

8. **Add payment routes and views**
   - Add routes in `urls.py` for:
     - Start payment
     - Payment callback/return
     - Payment cancellation
     - Webhook notification

9. **Update the checkout view**
   - The current checkout view in `checkout.py` immediately creates the order and redirects to its details page.
   - For online payment, it should create a pending order, initialize payment, and redirect the customer to the gateway.

10. **Update the checkout template**
    - The payment options are currently defined in `forms.py`.
    - Enable the Card/Bank Transfer options currently marked “coming soon”.
    - Change the submit button and display payment errors or redirects where required.

11. **Implement server-side payment verification**
    - Verify the transaction with the gateway API.
    - Confirm:
      - Payment reference
      - Amount
      - Currency
      - Order ID
      - Customer
    - Never trust only the browser callback.

12. **Implement a secure webhook**
    - Validate the provider’s signature or secret.
    - Make processing idempotent so repeated webhooks do not duplicate updates.
    - Mark the order paid only after successful verification.

13. **Handle stock and cart consistency**
    - Decide whether stock is reserved when the pending order is created or only after successful payment.
    - Restore stock and cancel unpaid orders when payment expires or fails.

14. **Update order/customer pages**
    - Show `Pending`, `Paid`, `Failed`, or `Cancelled` payment states in `order_detail.html`.

15. **Add tests**
    - Successful payment
    - Failed payment
    - Cancelled payment
    - Invalid signature
    - Wrong amount/reference
    - Duplicate webhook
    - Expired payment
    - Insufficient stock

16. **Configure production deployment**
    - Add production gateway keys to the hosting platform.
    - Configure the public HTTPS webhook URL.
    - Test with the provider’s test credentials before switching to live mode.
