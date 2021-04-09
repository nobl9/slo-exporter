FROM python:3
WORKDIR /usr/src/slo-exporter
COPY . .

ARG VERSION=0.0.48
ARG SOURCE=https://github.com/nobl9/sloctl/releases/download/$VERSION/sloctl-linux-$VERSION.zip
ARG TARGET=sloctl.zip
ARG TARGET_CHECKSUM=42e97b45f5c32c6d05c8919b3ba28ee9fed112c7ca64fd9e40e23390619a78f8
RUN curl -fLSs "$SOURCE" -o "$TARGET"
RUN sha256sum "$TARGET"
RUN echo "$TARGET_CHECKSUM *$TARGET" | sha256sum -c -
RUN unzip "$TARGET"
RUN rm "$TARGET"

RUN pip install -r requirements.txt

CMD printf "%s\n%s\n%s\n%s\ny\n" "$N9_PROJECT" "$N9_CLIENT_ID" "$N9_CLIENT_SECRET" "$N9_PROJECT" | ./sloctl add-context\
&& ./slo-exporter | sloctl apply -f -