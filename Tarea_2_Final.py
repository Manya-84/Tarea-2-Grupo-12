import json
from pydantic import BaseModel
from openai import OpenAI

client = OpenAI()

prompt_tokens = 0
completion_tokens = 0
tokens_used = 0
total_tokens_used = 0
total_prompt_tokens = 0
total_completion_tokens = 0

class Curriculum(BaseModel):
    class InfoAcademica(BaseModel):
        titulo: str
        institucion: str
        fecha_graduacion: int
    class InfoLaboral(BaseModel):
        empresa: str
        cargo: str
        responsabilidades: str
        fecha_inicio: int
        fecha_fin: int
    
    nombre: str
    email: str
    telefono: str
    info_academica: list[InfoAcademica]
    info_laboral: list[InfoLaboral]

    
def obtener_respuesta(mensajes):
    global total_tokens_used, total_prompt_tokens, total_completion_tokens
    response = client.chat.completions.create(
        model='gpt-4o',
        messages=mensajes,
        temperature=0,
        #max_tokens=1000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    # Obtener la respuesta del asistente
    respuesta = response.choices[0].message.content.strip()
    
    # Actualizar el contador de tokens
    tokens = response.usage
    total_prompt_tokens += response.usage.prompt_tokens
    total_completion_tokens += response.usage.completion_tokens
    total_tokens_used += response.usage.total_tokens
    
    return respuesta, tokens

def completar_json(mensajes):
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=mensajes,   
        response_format=Curriculum,
    )

    respuesta_json = completion.choices[0].message.parsed

    return respuesta_json

def main():
    mensajes = [
        {
            "role": "system",
            "content": ("""
                Eres un asistente en crear curriculums vitae.
                Para ello, debes solicitar la siguiente informacion:
                Información de Contacto: Nombre completo, número de teléfono,
                correo electrónico. (Todos obligatorios)
                
                Información Académica: Permite al usuario ingresar múltiples títulos,
                incluyendo el título obtenido, institución educativa y fecha de graduación
                para cada uno. (Al menos un elemento con todos los campos)
                
                Información Laboral: Permite al usuario ingresar múltiples experiencias
                laborales, incluyendo el puesto, empresa, responsabilidades y fechas de
                empleo para cada una. (Al menos un elemento con todos los campos)
                
                Una vez el usuario haya ingresado una información académica completa,
                debes preguntarle si quiere ingresar otra información académica antes de pasar a la Información Laboral.
                Debes hacer lo mismo con la información laboral.        
                
                Al comenzar di "Hola, soy tu asistente para crear un curriculum vitae. Para comenzar, dime tu nombre completo. Si deseas terminar antes escribe Salir, Terminar o Fin." 
                y luego comienza a solicitar la información. Cuando el usuario haya ingresado toda la información, dile que escriba Terminar para generar el curriculum.
            """)
        }
    ]
    while True:
        # Obtener respuestas del asistente
        respuesta_asistente, tokens = obtener_respuesta(mensajes)
        print("\nAsistente:", respuesta_asistente)
        print(f"Tokens usados en prompt: {tokens.prompt_tokens}")
        print(f"Tokens usados en completion: {tokens.completion_tokens}")
        print(f"Tokens totales usados: {tokens.total_tokens}")

        # Agregar la respuesta del asistente al historial de mensajes
        mensajes.append({"role": "assistant", "content": respuesta_asistente})

        # Obtener la respuesta del usuario
        respuesta_usuario = input("\nTu respuesta: ")

        # Verificar si el usuario desea terminar
        if respuesta_usuario.lower() in ["salir", "terminar", "fin"]:
            print("\nGenerando los archivos del curriculum.")
            break

        # Agregar la respuesta del usuario al historial de mensajes
        mensajes.append({"role": "user", "content": respuesta_usuario})

    # Al finalizar, pedir al asistente que genere el currículum completo
    mensajes.append(
        {
            "role": "user",
            "content": ("""
                Por favor, genera el currículum completo basado en la información proporcionada.
                Solo dame el curriculum, no me digas nada más.
            """)
        }
    )
    curriculo, tokens = obtener_respuesta(mensajes)

    # Obtiene el JSON
    json_final = completar_json(mensajes)

    # Convertir el objeto a una cadena JSON
    json_string = json_final.model_dump_json()

    # Convertir la cadena JSON a un diccionario
    json_dict = json.loads(json_string)

    # JSON formateado
    formatted_json = json.dumps(json_dict, indent=4)

    # Guardar el JSON formateado en un archivo .json
    with open('curriculum.json', 'w') as json_file:
        json_file.write(formatted_json)
    print("Archivo curriculum.json creado.")

    # Imprimir el currículum
    print("\nCurrículum generado:\n")
    print(curriculo)
    print(f"Tokens usados en prompt: {tokens.prompt_tokens}")
    print(f"Tokens usados en completion: {tokens.completion_tokens}")
    print(f"Tokens totales usados: {tokens.total_tokens}")

    # Guardar el curriculum en un archivo de texto
    with open('curriculum.txt', 'w') as text_file:
        text_file.write(curriculo)
    print("Archivo curriculum.txt creado.")


    # Consulta si desea agregar información adicional
    respuesta = input("¿Deseas agregar información adicional? (s/n): ")
    if respuesta.lower() in ["s", "si"]:
        mensajes.append(
            {
                "role": "user",
                "content": ("""
                    Ahora quiero agregar información adicional que consideres útil para
                    enriquecer el currículum (como motivaciones, habilidades, intereses, etc.)
                    Hazme mas preguntas para saber que agregar.
                    Recordar que si se quiere terminar se debe escribir 'salir', 'terminar' o 'fin'.
                """)
            }
        )
        while True:
            # Obtener respuestas del asistente
            respuesta_asistente, tokens = obtener_respuesta(mensajes)
            print("\nAsistente:", respuesta_asistente)
            print(f"Tokens usados en prompt: {tokens.prompt_tokens}")
            print(f"Tokens usados en completion: {tokens.completion_tokens}")
            print(f"Tokens totales usados: {tokens.total_tokens}")

            # Agregar la respuesta del asistente al historial de mensajes
            mensajes.append({"role": "assistant", "content": respuesta_asistente})

            # Obtener la respuesta del usuario
            respuesta_usuario = input("\nTu respuesta: ")

            # Verificar si el usuario desea terminar
            if respuesta_usuario.lower() in ["salir", "terminar", "fin"]:
                print("\nGenerando el curriculum con información adicional.")
                break

            # Agregar la respuesta del usuario al historial de mensajes
            mensajes.append({"role": "user", "content": respuesta_usuario})
        
        # Pedir que se genere el currículum completo con la información adicional
        mensajes.append(
            {
                "role": "user",
                "content": ("""
                    Por favor, genera el currículum completo basado en la información proporcionada.
                    Solo dame el curriculum, no me digas nada más.
                """)
            }
        )
        curriculo, tokens = obtener_respuesta(mensajes)
        print("\nCurrículum generado:\n")
        print(curriculo + "\n")
        print(f"Tokens usados en prompt: {tokens.prompt_tokens}")
        print(f"Tokens usados en completion: {tokens.completion_tokens}")
        print(f"Tokens totales usados: {tokens.total_tokens}")

    else:
        print("Ok, no agregaré información adicional")


    # Calcular el costo total
    costo_prompt_tokens = total_prompt_tokens * 0.00000125
    costo_completion_tokens = total_completion_tokens * 0.000005
    costo_total = costo_prompt_tokens + costo_completion_tokens

    # Imprimir el costo total en USD
    print("\nCosto total del proceso en USD:")
    print(f"Prompt tokens: ${costo_prompt_tokens:.6f}")
    print(f"Completion tokens: ${costo_completion_tokens:.6f}")
    print(f"Total: ${costo_total:.6f}")

    # Crear un diccionario con la información de los tokens y el costo
    tokens_info = {
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_tokens_used": total_tokens_used,
        "costo_prompt_tokens": costo_prompt_tokens,
        "costo_completion_tokens": costo_completion_tokens,
        "costo_total": costo_total
    }

    # Guardar la información en un archivo JSON
    with open('tokens_info.json', 'w') as json_file:
        json.dump(tokens_info, json_file, indent=4)
    print("Archivo tokens_info.json creado.")
    

if __name__ == '__main__':
    main()