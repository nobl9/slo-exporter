FROM python:3
WORKDIR /usr/src/slo-exporter
COPY . .
RUN curl -LJO https://github.com/nobl9/sloctl/raw/main/sloctl-linux-0.0.48.zip\
&& unzip sloctl-linux-0.0.48.zip\
&& rm sloctl-linux-0.0.48.zip

RUN pip install -r requirements.txt
CMD printf "%s\n%s\n%s\n%s\ny\n" "$N9_PROJECT" "$N9_CLIENT_ID" "$N9_CLIENT_SECRET" "$N9_PROJECT" | ./sloctl add-context\
&& ./slo-exporter | sloctl apply -f -