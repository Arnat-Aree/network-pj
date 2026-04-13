{{/* Generate full name */}}
{{- define "network-pj.fullname" -}}
{{- printf "%s" .Release.Name -}}
{{- end -}}
