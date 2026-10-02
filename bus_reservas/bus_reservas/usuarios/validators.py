import re


def documento_pasajero_valido(documento):
    """Accept valid Chilean RUTs and non-RUT passport identifiers."""
    normalized = re.sub(r'[\s.-]', '', documento).upper()
    looks_like_rut = (
        re.fullmatch(r'\d{1,8}[0-9K]', normalized) is not None
        and (
            re.search(r'[.-]', documento) is not None
            or re.fullmatch(r'\d{7,9}', normalized) is not None
            or normalized.endswith('K')
        )
    )
    if not looks_like_rut:
        return True

    body, verifier = normalized[:-1], normalized[-1]
    total = sum(
        int(digit) * weight
        for digit, weight in zip(reversed(body), (2, 3, 4, 5, 6, 7) * 2)
    )
    remainder = 11 - total % 11
    expected = '0' if remainder == 11 else 'K' if remainder == 10 else str(remainder)
    return verifier == expected
