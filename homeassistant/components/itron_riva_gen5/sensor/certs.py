# Hopefully this doesn't change. If it does,
# echo | openssl s_client -showcerts -servername ${IP} -connect ${IP}:8081 -xkey key.pem -xcert cert.pem -legacy_renegotiation -tls1_2 -cipher 'ALL:@SECLEVEL=0' 2>/dev/null | openssl x509 -inform pem -noout -text
# should get the new certificate
ITRON_CERT = """-----BEGIN CERTIFICATE-----
MIIBlDCCATmgAwIBAgIBATAKBggqhkjOPQQDAjArMQ4wDAYDVQQKDAVJdHJvbjEZ
MBcGA1UEAwwQSUVFRSAyMDMwLjUgUm9vdDAgFw0yMDEwMTYyMTI0NDhaGA85OTk5
MTIzMTIzNTk1OVowKzEOMAwGA1UECgwFSXRyb24xGTAXBgNVBAMMEElFRUUgMjAz
MC41IFJvb3QwWTATBgcqhkjOPQIBBggqhkjOPQMBBwNCAARpgDgTQhc5zoATkAs9
UWbT9uRau6GEb1R/1iPGLk+HAAOyAu3SkKHTwVGgzUPl73P9KMH9ZD4nSIQ5o2qJ
Mpuuo0wwSjAOBgNVHQ8BAf8EBAMCAQYwFAYDVR0gAQH/BAowCDAGBgRVHSAAMA8G
A1UdEwEB/wQFMAMBAf8wEQYDVR0OBAoECE4E78JKsqrnMAoGCCqGSM49BAMCA0kA
MEYCIQC4QuurwLz8N3Vp8vQJeTrXTSKplgtW3o+GLpUzbwt2awIhAPHKAZEk3d4c
55Ksb/AIXwrGwsrbsD75WmfKX9DjOc60
-----END CERTIFICATE-----"""