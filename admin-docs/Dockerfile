FROM squidfunk/mkdocs-material:latest

WORKDIR /docs

COPY docs/ ./docs/
COPY mkdocs.yml ./

RUN mkdir -p docs/assets/images

EXPOSE 8086

CMD ["serve", "--dev-addr=0.0.0.0:8086"]
