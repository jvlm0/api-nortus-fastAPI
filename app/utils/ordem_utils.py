

def split_obs(obs): 

    titulo = obs.split(" - ")[0] if obs else None
    descricao = obs.split(" - ")[1] if obs and " - " in obs else None

    return titulo, descricao