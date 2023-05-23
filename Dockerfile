FROM python:3
WORKDIR /usr/src/slo-exporter
COPY . .

ARG VERSION='0.0.87'
ARG SOURCE=https://github.com/nobl9/sloctl/releases/download/v$VERSION/sloctl-linux-$VERSION
ARG TARGET=/tmp/sloctl
ARG TARGET_CHECKSUM=a1251f663e68ccda131f9ccc3988e26e471f275ffdbb9a727272184c8caaf3b2
RUN curl -sL "$SOURCE" -o "$TARGET"
RUN sha256sum "$TARGET"
RUN echo "$TARGET_CHECKSUM *$TARGET" | sha256sum -c -
RUN chmod +x "$TARGET"
RUN mv /tmp/sloctl /usr/bin/

RUN pip install -r requirements.txt

CMD ./export.py > output.yaml | sloctl --config ./config.toml apply -f output.yaml