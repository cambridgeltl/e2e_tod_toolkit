FROM node:20.10.0-slim as builder

WORKDIR /usr/app

RUN rm -rf ./build && rm -rf ./node_modules

COPY . .

RUN npm ci -qy

CMD ["npm", "run", "build"]
