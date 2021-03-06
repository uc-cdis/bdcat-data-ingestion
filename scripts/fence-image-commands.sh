# This script is to be run from within a fence image

phs_from_file () {
  file_input=$1
  file_output=$2
  ELEMS=( )
  while IFS= read -r line || [ -n "$line" ]; do  
    line_split=(${line//,/ })
    ELEMS+=("${line_split[3]}")
  done < "$file_input"
  PHS_ARRAY=( )
  for i in "${ELEMS[@]}"; do
    if [[ $i == *"phs"* ]] && [[ ! " ${PHS_ARRAY[@]} " =~ " ${i} " ]]; then
      PHS_ARRAY+=($i)
    fi
  done
  ${arr[@]/*(^phs*)*/}
  echo ${PHS_ARRAY[*]} > $file_output
}

prune_commands_file () {
  EXISTING_GOOGLE_GROUPS_FILE=$1
  GOOGLE_GROUP_CREATE_SCRIPT_FILE=$2
  GOOGLE_GROUP_CREATE_SCRIPT_PRUNED_FILE=$3

  EXISTING_GROUPS=( )
  FOUND_GROUP_HEADER=0
  while IFS= read -r line || [ -n "$line" ]; do
    if [ $FOUND_GROUP_HEADER == 1 ]; then
      line_split=(${line//,/ })
      EXISTING_GROUPS+=("${line_split[2]}")
    fi

    if [ "$line" == 'GoogleBucketAccessGroup.email, Bucket.name, Project.auth_id' ]; then
      FOUND_GROUP_HEADER=1
    fi
  done < "$EXISTING_GOOGLE_GROUPS_FILE"

  NON_EXISTING_GROUPS=( )
  while IFS= read -r line || [ -n "$line" ]; do
    prune_this_group=0
    for i in "${EXISTING_GROUPS[@]}"; do
        if [[ $line == *"$i"* ]]; then
          prune_this_group=1
          echo "The group $i already exists. Skipping."
          break
        fi
    done
    if [ $prune_this_group == 0 ]; then
      NON_EXISTING_GROUPS+=("$line")
    fi
  done < "$GOOGLE_GROUP_CREATE_SCRIPT_FILE"

  printf "%s\n" "${NON_EXISTING_GROUPS[@]}" > $GOOGLE_GROUP_CREATE_SCRIPT_PRUNED_FILE

  echo "Pruned google groups commands:"
  cat $GOOGLE_GROUP_CREATE_SCRIPT_PRUNED_FILE
}

main () {
  existing_groups_file="google_list_authz_groups_output.txt"
  create_script_file="/data-ingestion-pipeline-output/google-groups.sh"
  pruned_commands_file_to_run="google-groups-pruned.sh"

  echo 'Received output from data-ingestion-pipeline:'
  ls /data-ingestion-pipeline-output/

  fence-create google-list-authz-groups > "$existing_groups_file"
  cat $existing_groups_file

  prune_commands_file $existing_groups_file $create_script_file $pruned_commands_file_to_run

  chmod +x $pruned_commands_file_to_run
  if [ "$CREATE_GOOGLE_GROUPS" == "true" ]; then
    echo "Creating google groups..."
    ./$pruned_commands_file_to_run
    echo "Ran creation commands. Now checking existing groups:"
    post_creation_existing_groups_file='post_creation_existing_groups.txt'
    file_expected_to_be_empty='post_creation_existing_vs_to_create_groups_diff.txt'
    fence-create google-list-authz-groups > "$post_creation_existing_groups_file"
    prune_commands_file $post_creation_existing_groups_file $pruned_commands_file_to_run $file_expected_to_be_empty
    groups_not_created=`cat $file_expected_to_be_empty`
    if [ ! -z "$groups_not_created" ]; then
      echo "Error: some google groups were not created:"
      group_names_not_created_file="group_names_not_created.txt"
      phs_from_file $file_expected_to_be_empty $group_names_not_created_file
      cat $group_names_not_created_file
      exit 1
    fi
  fi
}

if [ "${1}" != "--source-only" ]; then
    main "${@}"
fi