# blockexp

이 프로젝트는 [insight](https://github.com/bitpay/bitcore/tree/master/packages/insight), [insight-previous](https://github.com/bitpay/bitcore/tree/master/packages/insight-previous) 동작에 필요한 [bitcore-node](https://github.com/bitpay/bitcore/tree/master/packages/bitcore-node) 를 Python으로 포팅했습니다.

비동기 라이브러리 `asyncio`, `starlette`를 기반으로 작성되어 있습니다.

서버 실행시 자동으로 블록체인 데이터가 데이터베이스에 동기화됩니다.



## 서버 환경

- Python 3.7 (+ pipenv)
- MongoDB 4.0
- NodeJS v10
- Redis


## 필수 패키지

Ubuntu 19.04 LTS 기준으로 작성되어 있습니다.

- python3.7
- python3.7-dev
- build-essential
- libgmp3-dev
- libssl-dev


## 백엔드 서버 실행 방법

1. `pipenv sync`
2. `blockexp/config.py` 파일 편집
3. `pipenv run python -m blockexp`



## 프론트엔드 컴파일 방법

`insight-previous` 기준으로 작성되어 있습니다.

1. `bitcore` 폴더에서 `npm install` 
2. `bitcore/packages/insight-previous` 폴더에서 `npm install` 
3. `bitcore/packages/insight-previous` 폴더에서 `ENV=prod CHAIN=BTC NETWORK=mainnet API_PREFIX=http://localhost:8000/api npm run ionic:build --prod` 
   (필요시 적절하게 `CHAIN`, `NETWORK`, `API_PREFIX`를 변경하시면 됩니다.)

