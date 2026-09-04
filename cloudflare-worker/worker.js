// ACE Helper — Worker de validação de chave de acesso
//
// Esse código roda no Cloudflare, não no seu computador nem no .exe do
// usuário. É por isso que a lista de chaves fica realmente protegida:
// mesmo com o código-fonte do ACE Helper público no GitHub, ninguém
// consegue ver ou editar essa lista sem acesso à sua conta Cloudflare.
//
// ATENÇÃO: esse arquivo é só uma cópia de referência do que já está
// publicado no seu Worker (ace-helper-auth.contato-swfps.workers.dev).
// As chaves reais já configuradas lá NÃO são reproduzidas aqui — edite
// direto no painel do Cloudflare se precisar mudar algo.
//
// COMO ADICIONAR/REMOVER CHAVES:
// Edite o array VALID_KEYS abaixo e clique em "Deploy" de novo no
// painel do Cloudflare. Sem precisar mexer no app nem recompilar nada.

const VALID_KEYS = [
  "TROQUE-ESTA-CHAVE-1",
  "TROQUE-ESTA-CHAVE-2",
];

export default {
  async fetch(request) {
    if (request.method !== "POST") {
      return json({ valid: false, error: "Método não permitido" }, 405);
    }

    let body;
    try {
      body = await request.json();
    } catch (e) {
      return json({ valid: false, error: "JSON inválido" }, 400);
    }

    const key = (body.key || "").trim();
    const valid = VALID_KEYS.includes(key);

    return json({ valid });
  },
};

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}
