import time
import statistics
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from pqc.sign import dilithium2 as pqc_sign

ITERATIONS = 100
MESSAGE = b"benchmark_test_challenge_data_32bytes!!"

#ECC
print(f"ECC vs ML-DSA(Dilithium2) 벤치마크 ({ITERATIONS}회 반복)")
print("\nECC (SECP256R1)")

#키 생성
ecc_keygen_times = []
for _ in range(ITERATIONS):
    start = time.perf_counter()
    ecc_private = ec.generate_private_key(ec.SECP256R1())
    ecc_keygen_times.append((time.perf_counter() - start) * 1000)

ecc_public = ecc_private.public_key()

#서명
ecc_sign_times = []
ecc_signatures = []
for _ in range(ITERATIONS):
    start = time.perf_counter()
    sig = ecc_private.sign(MESSAGE, ec.ECDSA(hashes.SHA256()))
    ecc_sign_times.append((time.perf_counter() - start) * 1000)
    ecc_signatures.append(sig)

#검증
ecc_verify_times = []
for sig in ecc_signatures:
    start = time.perf_counter()
    ecc_public.verify(sig, MESSAGE, ec.ECDSA(hashes.SHA256()))
    ecc_verify_times.append((time.perf_counter() - start) * 1000)

ecc_pub_size = len(ecc_public.public_bytes(
    encoding=__import__("cryptography.hazmat.primitives.serialization", fromlist=["Encoding"]).Encoding.X962,
    format=__import__("cryptography.hazmat.primitives.serialization", fromlist=["PublicFormat"]).PublicFormat.UncompressedPoint
))
ecc_sig_size = len(ecc_signatures[0])

print(f"  키 생성 평균: {statistics.mean(ecc_keygen_times):.3f}ms")
print(f"  서명 평균:    {statistics.mean(ecc_sign_times):.3f}ms")
print(f"  검증 평균:    {statistics.mean(ecc_verify_times):.3f}ms")
print(f"  공개키 크기:  {ecc_pub_size} bytes")
print(f"  서명 크기:    {ecc_sig_size} bytes")

#ML-DSA
print("\nML-DSA (Dilithium2)")

#키 생성
pqc_keygen_times = []
for _ in range(ITERATIONS):
    start = time.perf_counter()
    pqc_public, pqc_secret = pqc_sign.keypair()
    pqc_keygen_times.append((time.perf_counter() - start) * 1000)

#서명
pqc_sign_times = []
pqc_signatures = []
for _ in range(ITERATIONS):
    start = time.perf_counter()
    sig = pqc_sign.sign(MESSAGE, pqc_secret)
    pqc_sign_times.append((time.perf_counter() - start) * 1000)
    pqc_signatures.append(sig)

#검증
pqc_verify_times = []
for sig in pqc_signatures:
    start = time.perf_counter()
    pqc_sign.verify(sig, MESSAGE, pqc_public)
    pqc_verify_times.append((time.perf_counter() - start) * 1000)

print(f"  키 생성 평균: {statistics.mean(pqc_keygen_times):.3f}ms")
print(f"  서명 평균:    {statistics.mean(pqc_sign_times):.3f}ms")
print(f"  검증 평균:    {statistics.mean(pqc_verify_times):.3f}ms")
print(f"  공개키 크기:  {len(pqc_public)} bytes")
print(f"  서명 크기:    {len(pqc_signatures[0])} bytes")

#비교결과
print("\n비교 결과 (ML-DSA / ECC 배율)")
print(f"  키 생성: {statistics.mean(pqc_keygen_times) / statistics.mean(ecc_keygen_times):.1f}배")
print(f"  서명:    {statistics.mean(pqc_sign_times) / statistics.mean(ecc_sign_times):.1f}배")
print(f"  검증:    {statistics.mean(pqc_verify_times) / statistics.mean(ecc_verify_times):.1f}배")
print(f"  공개키 크기: {len(pqc_public) / ecc_pub_size:.1f}배")
print(f"  서명 크기:   {len(pqc_signatures[0]) / ecc_sig_size:.1f}배")