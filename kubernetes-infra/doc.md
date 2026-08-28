🔐 1. HashiCorp Vault Commands (Mac setup)
Install
brew install vault
Start server (dev mode - easiest)
vault server -dev
Set environment
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN="s.xxxxx"
Check status
vault status
Initialize (ONLY first time)
vault operator init
Unseal (run 3 keys)
vault operator unseal <key1>
vault operator unseal <key2>
vault operator unseal <key3>
Login
vault login <root-token>
Enable secrets engine
vault secrets enable -path=secret kv-v2
Store secret (Docker example)
vault kv put secret/dockerhub username="user" password="pass"
Read secret
vault kv get secret/dockerhub
🌐 2. ngrok Commands (Expose Vault)
Install
brew install ngrok/ngrok/ngrok
Add token (REQUIRED)
ngrok config add-authtoken YOUR_TOKEN
Start tunnel
ngrok http 8200
Example output
https://abc123.ngrok-free.app → http://localhost:8200
Stop ngrok
CTRL + C
🛡️ 3. Trivy Commands (Vulnerability Scanner)
Install (Mac)
brew install aquasecurity/trivy/trivy
Scan image
trivy image sample-app:latest
JSON report (for Copa)
trivy image -f json -o trivy.json sample-app:latest
Scan filesystem
trivy fs .
Scan with severity filter
trivy image --severity HIGH,CRITICAL sample-app:latest
🔧 4. Copa Commands (Patch vulnerabilities)
Install
curl -fsSL https://raw.githubusercontent.com/project-copacetic/copacetic/main/install.sh | sudo bash
Check version
copa version
Patch image (IMPORTANT FLOW)
copa patch \
  -i sample-app:latest \
  -r trivy.json \
  -t sample-app:patched
Tag patched image
docker tag sample-app:patched youruser/sample-app:patched
Push patched image
docker push youruser/sample-app:patched
🐳 5. Docker Commands (CI/CD core)
Login
echo "password" | docker login -u "username" --password-stdin
Build
docker build -t sample-app:latest .
Tag
docker tag sample-app:latest user/sample-app:latest
Push
docker push user/sample-app:latest
🚀 6. Full CI/CD Flow (What you are building)




Kind cluster configuration

kind.yaml:

kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4

nodes:
  - role: control-plane

  - role: worker
    extraPortMappings:
      - containerPort: 30080
        hostPort: 80
      - containerPort: 30443
        hostPort: 443

Create:

kind create cluster --name dev --config kind.yaml

Verify:

kind get clusters
kubectl get nodes
2. Install NGINX Ingress

Your existing Helm installation uses:

controller:
  service:
    httpPort:
      nodePort: 30080
    httpsPort:
      nodePort: 30443

Check:

helm get values nginx-ingress -n nginx-ingress

Verify the Service:

kubectl get svc -n nginx-ingress

Expected:

nginx-ingress-controller   NodePort
80:30080/TCP
443:30443/TCP

Check controller:

kubectl get pods -n nginx-ingress

Logs:

kubectl logs -n nginx-ingress \
  <nginx-ingress-controller-pod> \
  --tail=100
3. Java application Service

Example:

apiVersion: v1
kind: Service
metadata:
  name: javaapp-service
  namespace: dev
spec:
  selector:
    app: javaapp
  ports:
    - port: 8080
      targetPort: 8080

Apply:

kubectl apply -f java-service.yaml

Check:

kubectl get svc -n dev

Check endpoints:

kubectl get endpoints -n dev javaapp-service

You should see:

10.x.x.x:8080
4. HTTP Ingress

Your working Ingress:

apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: javaapp-service
  namespace: dev
spec:
  ingressClassName: nginx

  rules:
    - host: myapp1.local
      http:
        paths:
          - path: /sample
            pathType: Prefix
            backend:
              service:
                name: javaapp-service
                port:
                  number: 8080

Apply:

kubectl apply -f java-ingress.yaml

Verify:

kubectl get ingress -n dev
kubectl describe ingress javaapp-service -n dev
5. Create local Root CA

This is the CA that your Mac/browser will trust.

Create directory:

mkdir -p ~/local-ca
cd ~/local-ca

Generate Root CA private key:

openssl genrsa -out my-local-root-ca.key 4096

Generate Root CA certificate:

openssl req -x509 \
  -new \
  -nodes \
  -key my-local-root-ca.key \
  -sha256 \
  -days 3650 \
  -out my-local-root-ca.crt \
  -subj "/C=US/ST=NC/O=MyLocalCA/CN=My Local Root CA"

Verify:

openssl x509 \
  -in my-local-root-ca.crt \
  -noout \
  -subject \
  -issuer \
  -dates

Check that it is a CA:

openssl x509 \
  -in my-local-root-ca.crt \
  -noout \
  -text | grep -A4 "Basic Constraints"

You should have:

CA:TRUE
6. Create certificate for myapp1.local

Create OpenSSL config:

cat > myapp1.local.cnf <<'EOF'
[req]
default_bits = 2048
prompt = no
default_md = sha256
req_extensions = req_ext
distinguished_name = dn

[dn]
C = US
ST = NC
O = MyLocal
CN = myapp1.local

[req_ext]
subjectAltName = @alt_names

[alt_names]
DNS.1 = myapp1.local
EOF

Generate server private key:

openssl genrsa \
  -out myapp1.local.key 2048

Generate CSR:

openssl req \
  -new \
  -key myapp1.local.key \
  -out myapp1.local.csr \
  -config myapp1.local.cnf

Sign it with your Root CA:

openssl x509 \
  -req \
  -in myapp1.local.csr \
  -CA my-local-root-ca.crt \
  -CAkey my-local-root-ca.key \
  -CAcreateserial \
  -out myapp1.local.crt \
  -days 825 \
  -sha256 \
  -extensions req_ext \
  -extfile myapp1.local.cnf

Verify:

openssl x509 \
  -in myapp1.local.crt \
  -noout \
  -subject \
  -issuer \
  -dates

Verify SAN:

openssl x509 \
  -in myapp1.local.crt \
  -noout \
  -text | grep -A2 "Subject Alternative Name"

You should see:

DNS:myapp1.local
7. Create Kubernetes TLS Secret

Create the secret:

kubectl create secret tls myapp1-tls \
  -n dev \
  --cert=myapp1.local.crt \
  --key=myapp1.local.key

Verify:

kubectl get secret myapp1-tls -n dev
8. Add TLS to Ingress

Update your Ingress:

apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: javaapp-service
  namespace: dev
spec:
  ingressClassName: nginx

  tls:
    - hosts:
        - myapp1.local
      secretName: myapp1-tls

  rules:
    - host: myapp1.local
      http:
        paths:
          - path: /sample
            pathType: Prefix
            backend:
              service:
                name: javaapp-service
                port:
                  number: 8080

Apply:

kubectl apply -f java-ingress.yaml

Verify:

kubectl describe ingress javaapp-service -n dev
9. Configure /etc/hosts

On your Mac:

sudo vi /etc/hosts

For the same Mac running Colima/kind:

127.0.0.1 myapp1.local

Verify:

cat /etc/hosts | grep myapp1.local

Test:

ping -c 1 myapp1.local
10. Verify kind/Docker port mapping

Check:

docker ps --format "table {{.Names}}\t{{.Ports}}"

Expected:

dev-worker   0.0.0.0:80->30080/tcp, 0.0.0.0:443->30443/tcp

Also:

docker port dev-worker

Expected:

30080/tcp -> 0.0.0.0:80
30443/tcp -> 0.0.0.0:443
11. Test NGINX from inside Kubernetes

This was one of our successful tests:

kubectl run test-curl --rm -it \
  --image=curlimages/curl \
  --restart=Never -- \
  curl -v \
  -H "Host: myapp1.local" \
  http://nginx-ingress-controller.nginx-ingress.svc.cluster.local/sample

You got:

HTTP/1.1 302 Found
Location: /sample/

That confirmed NGINX routing.

12. Test directly from the kind worker
docker exec dev-worker curl -v \
  -H "Host: myapp1.local" \
  http://127.0.0.1:30080/sample

Expected:

HTTP/1.1 302 Found
Location: /sample/
13. Test HTTPS

From your Mac:

curl -vk https://myapp1.local/sample/

You should see:

SSL connection using TLSv1.3

and:

HTTP/1.1 200 OK

with your Java response:

<h1>blue deployment!!</h1>
14. Trust the Root CA on macOS

This was the final piece that removed your browser warning.

Use the Root CA certificate:

my-local-root-ca.crt

Do not import:

myapp1.local.crt

as the Root CA.

You can add the Root CA to the System keychain with:

sudo security add-trusted-cert \
  -d \
  -r trustRoot \
  -k /Library/Keychains/System.keychain \
  ~/local-ca/my-local-root-ca.crt

Verify:

security find-certificate \
  -a \
  -c "My Local Root CA" \
  /Library/Keychains/System.keychain

Then test without -k:

curl -v https://myapp1.local/sample/

You should no longer get:

unable to get local issuer certificate
15. Final browser URL

Use:

https://myapp1.local/sample/

Your complete traffic flow is:

                    Mac
                     │
                     │ https://myapp1.local/sample/
                     ▼
              /etc/hosts
            127.0.0.1
                     │
                     ▼
              Docker / Colima
                     │
                     ▼
               kind worker
             Host :443
                     │
                     ▼
             NodePort :30443
                     │
                     ▼
           NGINX Ingress Controller
                     │
             TLS termination
                     │
             Host: myapp1.local
                     │
             Path: /sample/
                     ▼
             javaapp-service:8080
                     │
                     ▼
                 Java Pod
                     │
                     ▼
             HTTP 200 / Application
For your second domain

You can repeat the same pattern:

myapp1.local → Java application
myapp2.local → Backend application

with separate Ingress rules and, ideally, separate TLS certificates or a single certificate containing both DNS names. This gives you one NGINX Ingress load-balancer/reverse-proxy entry point with host-based routing to different applications.

Files, images, and data analysis are unavailable until usage resets at 8:12 PM. Continue chatting with text only, or upgrade for more access.


#####haproxy

Step 3 — Kind port mapping

Your Kind worker should expose only HAProxy externally.

Your kind.yaml should look like:

kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4

nodes:
  - role: control-plane

  - role: worker
    extraPortMappings:
      - containerPort: 30080
        hostPort: 80
        protocol: TCP

      - containerPort: 30443
        hostPort: 443
        protocol: TCP

Important: these NodePorts belong to HAProxy, not NGINX Ingress.

If the existing Kind cluster was created with different mappings, changing kind.yaml does not change the existing cluster. You would need to recreate the cluster.

Step 4 — Create HAProxy namespace
kubectl create namespace haproxy

If it already exists, that's okay.

kubectl get ns haproxy
Step 5 — Create HAProxy TLS certificates

Create a directory:

mkdir -p ~/haproxy-certs
cd ~/haproxy-certs

We will create a local Root CA.

5.1 Root CA key
openssl genrsa -out rootCA.key 4096
5.2 Root CA certificate
openssl req -x509 -new -nodes \
  -key rootCA.key \
  -sha256 \
  -days 3650 \
  -out rootCA.crt \
  -subj "/C=US/ST=NC/L=Raleigh/O=MyLocalCA/CN=My Local Root CA"
Step 6 — Create certificate for multiple hosts

Create:

vi server.ext

Put:

authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage=digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth

subjectAltName=@alt_names

[alt_names]
DNS.1=myapp1.local
DNS.2=myapp2.local

You can later add:

DNS.3=api.local
DNS.4=java.local
DNS.5=backend.local
Step 7 — Create server private key
openssl genrsa -out server.key 2048
Step 8 — Create CSR
openssl req -new \
  -key server.key \
  -out server.csr \
  -subj "/C=US/ST=NC/L=Raleigh/O=MyLocal/CN=myapp1.local"
Step 9 — Sign certificate
openssl x509 -req \
  -in server.csr \
  -CA rootCA.crt \
  -CAkey rootCA.key \
  -CAcreateserial \
  -out server.crt \
  -days 825 \
  -sha256 \
  -extfile server.ext

Now you have:

server.key
server.crt
Step 10 — Verify
openssl verify -CAfile rootCA.crt server.crt

Expected:

server.crt: OK

Check SAN:

openssl x509 -in server.crt -text -noout | grep -A1 "Subject Alternative Name"

You should see:

DNS:myapp1.local, DNS:myapp2.local
Step 11 — Create HAProxy PEM

HAProxy needs certificate + private key together.

cat server.crt server.key > haproxy.pem

Check:

ls -l haproxy.pem
Step 12 — Create Kubernetes TLS Secret
kubectl create secret generic haproxy-tls \
  -n haproxy \
  --from-file=haproxy.pem=haproxy.pem

Check:

kubectl get secret haproxy-tls -n haproxy
Step 13 — Create HAProxy ConfigMap

Create:

vi haproxy-config.yaml

Use:

apiVersion: v1
kind: ConfigMap
metadata:
  name: haproxy-config
  namespace: haproxy

data:
  haproxy.cfg: |
    global
        log stdout format raw local0

    defaults
        mode http
        log global
        option httplog

        timeout connect 5s
        timeout client 30s
        timeout server 30s

    frontend http_front
        bind :80
        default_backend nginx_ingress

    frontend https_front
        bind :443 ssl crt /etc/haproxy/certs/
        default_backend nginx_ingress

    backend nginx_ingress
        balance roundrobin
        server nginx-ingress nginx-ingress-controller.nginx-ingress.svc.cluster.local:80 check

The important line is:

bind :443 ssl crt /etc/haproxy/certs/

HAProxy will look in that directory for certificates and use SNI.

Step 14 — Apply ConfigMap
kubectl apply -f haproxy-config.yaml

Check:

kubectl get configmap -n haproxy
Step 15 — Create HAProxy Deployment

Create:

vi haproxy-deployment.yaml

Use:

apiVersion: apps/v1
kind: Deployment
metadata:
  name: haproxy
  namespace: haproxy

spec:
  replicas: 1

  selector:
    matchLabels:
      app: haproxy

  template:
    metadata:
      labels:
        app: haproxy

    spec:
      containers:
        - name: haproxy
          image: haproxy:3.0

          ports:
            - name: http
              containerPort: 80

            - name: https
              containerPort: 443

          volumeMounts:
            - name: config
              mountPath: /usr/local/etc/haproxy/haproxy.cfg
              subPath: haproxy.cfg

            - name: tls
              mountPath: /etc/haproxy/certs
              readOnly: true

      volumes:
        - name: config
          configMap:
            name: haproxy-config

        - name: tls
          secret:
            secretName: haproxy-tls

Apply:

kubectl apply -f haproxy-deployment.yaml

Check:

kubectl get pods -n haproxy

You want:

haproxy-xxxxx   1/1   Running
Step 16 — Verify HAProxy is listening
kubectl exec -n haproxy deploy/haproxy -- ss -lntp

You should see:

0.0.0.0:80
0.0.0.0:443
Step 17 — Create HAProxy Service

Create:

vi haproxy-service.yaml

Use:

apiVersion: v1
kind: Service
metadata:
  name: haproxy
  namespace: haproxy

spec:
  type: NodePort

  selector:
    app: haproxy

  ports:
    - name: http
      port: 80
      targetPort: 80
      nodePort: 30080

    - name: https
      port: 443
      targetPort: 443
      nodePort: 30443

Apply:

kubectl apply -f haproxy-service.yaml

Check:

kubectl get svc -n haproxy

Expected:

haproxy   NodePort   ...   80:30080/TCP,443:30443/TCP
Step 18 — NGINX Ingress should be ClusterIP

Now your NGINX Ingress should not be externally exposed.

Check:

kubectl get svc -n nginx-ingress

It should show:

nginx-ingress-controller   ClusterIP   ...   80/TCP,443/TCP

If it is still NodePort, change the Helm values.

Your values should be:

controller:
  service:
    type: ClusterIP

Then:

helm upgrade nginx-ingress nginx-stable/nginx-ingress \
  -n nginx-ingress \
  -f values.yaml
Step 19 — Your NGINX Ingress

Your existing Ingress can remain:

apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: javaapp-service
  namespace: dev

spec:
  ingressClassName: nginx

  rules:
    - host: myapp1.local

      http:
        paths:
          - path: /sample
            pathType: Prefix

            backend:
              service:
                name: javaapp-service
                port:
                  number: 8080

NGINX receives:

Host: myapp1.local

and routes it to:

javaapp-service:8080
Step 20 — Add your hosts to /etc/hosts

On your Mac:

sudo vi /etc/hosts

For your Kind setup, if using localhost:

127.0.0.1 myapp1.local
127.0.0.1 myapp2.local

Check:

cat /etc/hosts | grep local
Step 21 — Test HTTP through HAProxy

First:

curl -v http://myapp1.local/sample/

Traffic should be:

Mac :80
   ↓
Kind worker :30080
   ↓
HAProxy :80
   ↓
NGINX Ingress ClusterIP :80
   ↓
javaapp-service:8080
Step 22 — Test HTTPS through HAProxy

Now:

curl -vk https://myapp1.local/sample/

The path is:

Mac :443
   ↓
Kind worker :30443
   ↓
HAProxy :443
   ↓
TLS termination
   ↓
NGINX Ingress ClusterIP :80
   ↓
javaapp-service:8080

You should get:

HTTP/1.1 200 OK
Step 23 — Verify HAProxy received the request

Terminal 1:

kubectl logs -n haproxy -l app=haproxy -f

Terminal 2:

curl -vk https://myapp1.local/sample/

HAProxy should show an HTTP request such as:

"GET /sample/ HTTP/1.1"
Step 24 — Add your second application

Suppose you have:

myapp2.local

Add another Ingress:

apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: backend
  namespace: dev

spec:
  ingressClassName: nginx

  rules:
    - host: myapp2.local

      http:
        paths:
          - path: /
            pathType: Prefix

            backend:
              service:
                name: backend-service
                port:
                  number: 8080

Then:

kubectl apply -f backend-ingress.yaml

Now:

https://myapp1.local/sample/
        ↓
HAProxy
        ↓
NGINX
        ↓
javaapp-service


https://myapp2.local/
        ↓
HAProxy
        ↓
NGINX
        ↓
backend-service

You do NOT change HAProxy for every new application.

That's the key benefit of this architecture.

Final architecture
                         Internet / Browser
                                |
                         :80 / :443
                                |
                                v
                       +----------------+
                       |    HAProxy     |
                       |  :80 / :443   |
                       |                |
                       | TLS + SNI      |
                       +-------+--------+
                               |
                               | HTTP
                               v
                  +--------------------------+
                  |    NGINX Ingress         |
                  |       ClusterIP          |
                  +------------+-------------+
                               |
              +----------------+----------------+
              |                |                |
              v                v                v
        myapp1.local     myapp2.local      api.local
              |                |                |
              v                v                v
       javaapp-service   backend-service    api-service

One HAProxy entry point. One :443. NGINX handles the 10+ hostname/path routing.

Suggested based on your interests
Ad
