Save4Life API and admin interface
=================================

This API provides the back-end for the Save4Life USSD interface. It also include a admin interface that can be used to create quizzes, generate vouchers and see other information related to users and transactions.

If you are looking to setup the whole Save4Life application, please see documentation [here](https://github.com/dirkcuys/save4life-vumi)

# Running the API

## Docker image

The Dockerfile describe an image that can be used to run the API. To run the image, you need to link it to a running postgres, RabbitMQ and Junebug container.

You also need to pass it the following environment variables:

- `DATABASE_URL`
- `BROKER_URL`
- `JUNEBUG_SMS_URL`
- `AIRTIME_WSDL_URL`
- `AIRTIME_TERMINAL_NUMBER`
- `AIRTIME_MSISDN`
- `AIRTIME_PIN`

You can build the image using the Dockerfile, or you can get the latest image from the [Docker Hub](https://hub.docker.com/r/dirkcuys/save4life/)

